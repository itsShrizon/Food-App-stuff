import subprocess
import time
import sys
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

# ==============================================================================
# 1. Models & Configuration
# ==============================================================================

@dataclass
class Scenario:
    name: str
    description: str
    steps: List[str]  # List of user inputs in order
    expected_data_subset: Dict[str, Any]  # Key-values that MUST be present in final JSON
    strict: bool = False  # If True, expected_data matches exact values

CLI_SCRIPT = "cli_onboarding.py"

# ==============================================================================
# 2. Scenarios
# ==============================================================================

SCENARIOS = [
    # --- Category 1: Standard / Happy Path (5 scenarios) ---
    Scenario(
        name="Standard_Male_Lose",
        description="Basic male user wanting to lose weight, metric units.",
        steps=[
            "Male",
            "1990-01-01",
            "180 cm",
            "90 kg",
            "Lose weight, Normal speed", # Combined to handle flow variability
            "80 kg",
            "Moderate",
            "Yes", # Confirm macros
            "None" # Dietary
        ],
        expected_data_subset={"gender": "male", "goal": "lose_weight", "current_weight": 90}
    ),
    Scenario(
        name="Standard_Female_Gain",
        description="Basic female user wanting to gain weight, imperial units.",
        steps=[
            "Female",
            "2000-05-20",
            "5.5 feet",
            "110 lbs",
            "Gain weight, Slow speed", # Combined
            "125 lbs",
            "Active",
            "Yes",
            "None"
        ],
        expected_data_subset={"gender": "female", "goal": "gain_weight", "current_weight_unit": "lb"}
    ),
    Scenario(
        name="Standard_Other_Maintain",
        description="Non-binary user wanting maintenance.",
        steps=[
            "Other",
            "1985-12-12",
            "170 cm",
            "70 kg",
            "Maintain",
            "70 kg",
            "Normal", # Speed might be skipped for maintain, but providing it just in case or if asked
            "Sedentary",
            "Yes",
            "Vegan"
        ],
        expected_data_subset={"gender": "others", "goal": "maintain"}
    ),
     Scenario(
        name="Standard_Male_Cut_Fast",
        description="Male user wanting to cut fast.",
        steps=[
            "Male",
            "1995-03-15",
            "185 cm",
            "95 kg",
            "Cut, Fast",
            "85 kg",
            "Very active",
            "Yes",
            "No allergies"
        ],
        expected_data_subset={"target_speed": "fast", "activity_level": "active"}
    ),
    Scenario(
        name="Standard_Female_Bulk_Slow",
        description="Female user wanting to bulk slowly.",
        steps=[
            "Female",
            "1998-07-07",
            "165 cm",
            "60 kg",
            "Bulk, Slow",
            "65 kg",
            "Lightly active",
            "Yes",
            "None"
        ],
        expected_data_subset={"target_speed": "slow", "activity_level": "light"}
    ),

    # --- Category 2: Grammar & Typos (5 scenarios) ---
    Scenario(
        name="Grammar_Me_Wan_Loose",
        description="Poor grammar: 'me wan loose w8'.",
        steps=[
            "mail", # Male
            "1990-01-01",
            "180 cm",
            "90 kg",
            "80 kg",
            "me wan loose w8", # Lose weight
            "nrml", # Normal
            "modrate", # Moderate
            "yup",
            "nun"
        ],
        expected_data_subset={"gender": "male", "goal": "lose_weight"}
    ),
    Scenario(
        name="Grammar_Im_20_Five",
        description="Age written as text.",
        steps=[
            "female",
            "im 20 five", # Age 25 -> Should convert to DoB
            "170 cm",
            "70 kg",
            "60 kg",
            "lose",
            "normal",
            "active",
            "sure",
            "none"
        ],
        expected_data_subset={"age": 25}
    ),
    Scenario(
        name="Typo_Gendr_Wight",
        description="Typos in gender and weight.",
        steps=[
            "femail",
            "2001-01-01",
            "160 cm",
            "60 kgg", # Typo
            "55 kgs",
            "loos",
            "fasqt", # Fast
            "sedentri",
            "ok",
            "na"
        ],
        expected_data_subset={"gender": "female", "current_weight": 60, "target_speed": "fast"}
    ),
    Scenario(
        name="Colloquial_Units",
        description="Using 'kilo' instead of kg.",
        steps=[
            "guy",
            "2002-02-02",
            "180",
            "cm", # Clarification
            "80 kilos",
            "75",
            "kg", # Clarification
            "drop weight",
            "asap", # Fast
            "couch potato", # Sedentary
            "y",
            "nope"
        ],
        expected_data_subset={"gender": "male", "goal": "lose_weight", "activity_level": "sedentary"}
    ),
    Scenario(
        name="Slang_Affirmations",
        description="Using slang for confirmations.",
        steps=[
            "M",
            "1999-09-09",
            "175 cm",
            "75 kg",
            "80 kg",
            "get big", # Gain
            "steady", # Normal/Slow depending on LLM interpretation, sticking to Normal intent
            "gym rat", # Active
            "looks dope", # Yes
            "nah"
        ],
        expected_data_subset={"goal": "gain_weight"}
    ),

    # --- Category 3: Multiple Fields (5 scenarios) ---
    Scenario(
        name="Multi_Intro",
        description="Providing gender, age, height, weight in first message.",
        steps=[
            "Hi, I'm a 25 year old male, 180cm, 80kg",
            "75 kg", # Target
            "lose",
            "normal",
            "moderate",
            "yes",
            "none"
        ],
        expected_data_subset={"gender": "male", "age": 25, "current_height": 180}
    ),
    Scenario(
        name="Multi_Goal_Speed",
        description="Providing goal and speed together.",
        steps=[
            "Female",
            "2000-01-01",
            "165 cm",
            "60 kg",
            "55 kg",
            "I want to lose weight quickly",
            "moderate",
            "yes",
            "none"
        ],
        expected_data_subset={"goal": "lose_weight", "target_speed": "fast"}
    ),
    Scenario(
        name="Multi_DoB_Height",
        description="Providing DoB and Height together.",
        steps=[
            "Male",
            "born 1990-05-05, 175cm tall",
            "85 kg",
            "80 kg",
            "lose",
            "normal",
            "sedentary",
            "yes",
            "none"
        ],
        expected_data_subset={"date_of_birth": "1990-05-05", "current_height": 175}
    ),
    Scenario(
        name="Multi_All_Physical",
        description="Big dump of physical stats.",
        steps=[
            "Age 30, Male, 180cm, 90kg, target 85kg",
            "lose", # Goal might be inferred from target<current, but flow might ask
            "normal",
            "light",
            "yes",
            "none"
        ],
        expected_data_subset={"age": 30, "current_weight": 90, "target_weight": 85}
    ),
    Scenario(
        name="Multi_Activity_Macros",
        description="Activity and preemptive confirmation (might be tricky).",
        steps=[
            "Male",
            "1995-01-01",
            "180 cm",
            "80 kg",
            "80 kg",
            "maintain",
            "normal",
            "I am very active and these macros look good", # Trying to confirm macros early? (Flow might not allow)
            "yes", # Re-confirm if flow insists
            "none"
        ],
        expected_data_subset={"activity_level": "active"}
    ),

    # --- Category 4: Units & formats (5 scenarios) ---
    Scenario(
        name="Units_Feet_Inches_Separate",
        description="5 feet 10 inches.",
        steps=[
            "Male",
            "1990-01-01",
            "5 feet 10 inches",
            "180 lbs",
            "170 lbs",
            "lose",
            "normal",
            "moderate",
            "yes",
            "none"
        ],
        expected_data_subset={} # Height logic is complex, just ensure it completes
    ),
    Scenario(
        name="Units_Decimal_Feet",
        description="5.9 feet.",
        steps=[
            "Female",
            "2000-01-01",
            "5.9 feet",
            "130 lbs",
            "120 lbs",
            "lose",
            "normal",
            "moderate",
            "yes",
            "none"
        ],
        expected_data_subset={"current_height_unit": "in"}
    ),
    Scenario(
        name="Units_Mixed_Metric_Imperial",
        description="CM for height, Lbs for weight.",
        steps=[
            "Male",
            "1990-01-01",
            "180 cm",
            "180 lbs",
            "170 lbs",
            "lose",
            "normal",
            "active",
            "yes",
            "none"
        ],
        expected_data_subset={"current_weight_unit": "lb", "current_height_unit": "cm"}
    ),
    Scenario(
        name="Units_Stone",
        description="Using Stone (might fail if not supported, but good test).",
        steps=[
            "Male",
            "1990-01-01",
            "180 cm",
            "12 stone", # Check if LLM handles stone
            "11 stone",
            "lose",
            "normal",
            "moderate",
            "yes",
            "none"
        ],
        expected_data_subset={} # Expect completion, maybe LLM converts stone
    ),
    Scenario(
        name="Date_Format_Wordy",
        description="June 15th 1995.",
        steps=[
            "Female",
            "June 15th 1995",
            "165 cm",
            "60 kg",
            "60 kg",
            "maintain",
            "normal",
            "light",
            "yes",
            "none"
        ],
        expected_data_subset={"date_of_birth": "1995-06-15"}
    ),

    # --- Category 5: Dietary Preferences (5 scenarios) ---
    Scenario(
        name="Dietary_Vegan",
        description="Vegan preference.",
        steps=[
            "Male", "1990-01-01", "180 cm", "80 kg", "80 kg", "maintain", "normal", "moderate", "yes",
            "Vegan"
        ],
        expected_data_subset={"vegan": True}
    ),
    Scenario(
        name="Dietary_Multiple",
        description="Vegan and Gluten Free.",
        steps=[
            "Female", "2000-01-01", "165 cm", "60 kg", "60 kg", "maintain", "normal", "moderate", "yes",
            "I am vegan and also gluten free"
        ],
        expected_data_subset={"vegan": True, "gluten_free": True}
    ),
    Scenario(
        name="Dietary_Allergies_Phrasing",
        description="'I am allergic to nuts'.",
        steps=[
            "Male", "1990-01-01", "180 cm", "80 kg", "80 kg", "maintain", "normal", "moderate", "yes",
            "allergic to nuts"
        ],
        expected_data_subset={"nut_free": True}
    ),
    Scenario(
        name="Dietary_Exclusion",
        description="'No dairy'.",
        steps=[
            "Male", "1990-01-01", "180 cm", "80 kg", "80 kg", "maintain", "normal", "moderate", "yes",
            "No dairy please"
        ],
        expected_data_subset={"dairy_free": True}
    ),
    Scenario(
        name="Dietary_Celiac",
        description="'I have celiac disease'.",
        steps=[
            "Male", "1990-01-01", "180 cm", "80 kg", "80 kg", "maintain", "normal", "moderate", "yes",
            "I have celiac disease"
        ],
        expected_data_subset={"gluten_free": True}
    ),

    # --- Category 6: Edge / Conversational (8 scenarios) ---
    Scenario(
        name="Edge_Refusal_Then_Answer",
        description="User refuses first, then answers.",
        steps=[
            "Why do you need to know?", # Gender
            "Male",
            "1990-01-01",
            "180 cm",
            "80 kg",
            "80 kg",
            "maintain",
            "normal",
            "moderate",
            "yes",
            "none"
        ],
        expected_data_subset={"gender": "male"}
    ),
    Scenario(
        name="Edge_Unsure_Goal",
        description="User says 'idk' to goal.",
        steps=[
            "Female",
            "2000-01-01",
            "165 cm",
            "60 kg",
            "58 kg",
            "Idk, maybe lose a bit?",
            "normal",
            "moderate",
            "yes",
            "none"
        ],
        expected_data_subset={"goal": "lose_weight"}
    ),
    Scenario(
        name="Edge_Corrections",
        description="User corrects themselves.",
        steps=[
            "Male",
            "1990-01-01",
            "170 cm... wait actually 180 cm",
            "80 kg",
            "80 kg",
            "maintain",
            "normal",
            "moderate",
            "yes",
            "none"
        ],
        expected_data_subset={"current_height": 180}
    ),
    Scenario(
        name="Edge_Long_Story",
        description="User tells a story.",
        steps=[
            "Well I used to be a quarterback in highschool so I identify as a Male",
            "Back in 1990 I was born on Jan 1st",
            "I stand tall at 180 cm",
            "The scale says 90 kg unfortunately",
            "I want to get back to 80 kg",
            "Gotta get that lose weight grind",
            "normal speed",
            "I walk my dog so light activity",
            "Looks good",
            "No food restrictions"
        ],
        expected_data_subset={"gender": "male", "activity_level": "light"}
    ),
    Scenario(
        name="Edge_Negative_Dietary",
        description="'Nothing really'.",
        steps=[
            "Male", "1990-01-01", "180 cm", "80 kg", "80 kg", "maintain", "normal", "moderate", "yes",
            "Nothing really"
        ],
        expected_data_subset={"none": True}
    ),
    Scenario(
        name="Edge_Partial_Activity",
        description="'I work in an office but run daily'.",
        steps=[
            "Male", "1990-01-01", "180 cm", "80 kg", "80 kg", "maintain", "normal",
            "I work in an office but run daily", # Should be Active/Moderate
            "yes",
            "none"
        ],
        expected_data_subset={"activity_level": "active"} # Or moderate
    ),
    Scenario(
        name="Edge_Metric_Abbreviations",
        description="'cm', 'kg' without space.",
        steps=[
             "Male", "1990-01-01", "180cm", "80kg", "80kg", "maintain", "normal", "moderate", "yes", "none"
        ],
        expected_data_subset={"current_height": 180}
    ),
    Scenario(
        name="Edge_Caps_Lock",
        description="ALL CAPS INPUT.",
        steps=[
             "MALE", "1990-01-01", "180 CM", "80 KG", "80 KG", "MAINTAIN", "NORMAL", "MODERATE", "YES", "NONE"
        ],
        expected_data_subset={"gender": "male"}
    )
]

# ==============================================================================
# 3. Test Runner
# ==============================================================================

class TestRunner:
    def __init__(self, scenarios: List[Scenario]):
        self.scenarios = scenarios
        self.results = []

    def run_scenario(self, scenario: Scenario):
        print(f"\nRunning Scenario: {scenario.name}")
        print(f"Description: {scenario.description}")
        
        # Start the CLI process
        process = subprocess.Popen(
            [sys.executable, CLI_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=".",
            bufsize=0 # Unbuffered for simpler interaction
        )

        output_buffer = ""
        final_json = None
        current_step_idx = 0
        
        try:
            # Prepare all inputs
            full_input_str = "\n".join(scenario.steps) + "\n"
            print(f"[TEST]: Sending inputs:\n{full_input_str}")
            
            # Use communicate to send input and read output
            # This handles the blocking nature of input() by filling the pipe
            stdout_data, stderr_data = process.communicate(input=full_input_str, timeout=120)
            
            print(f"[CLI Output Wrapper]:\n{stdout_data}")

            # Check logic
            # stdout_data will contain all the output.
            # We verify scenarios by looking for "ONBOARDING COMPLETE!" and parsing the JSON.
            
            if "ONBOARDING COMPLETE!" in stdout_data:
                # Extract JSON
                # It is printed at the end: "DB-Ready JSON Output:\n{...}"
                json_match = re.search(r"DB-Ready JSON Output:\s*(\{.*\})", stdout_data, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    final_json = json.loads(json_str)
                    
                    # Flatten 'onboarding' key if present, as scenarios expect direct access
                    if 'onboarding' in final_json and isinstance(final_json['onboarding'], dict):
                        final_json.update(final_json['onboarding'])
                    
                    # Also flatten 'dietary_preferences' for easier validation
                    if 'dietary_preferences' in final_json and isinstance(final_json['dietary_preferences'], dict):
                        final_json.update(final_json['dietary_preferences'])
                else:
                    print("ERROR: Could not find JSON output logic.")
            else:
                print(f"ERROR: Scenario did not complete. stderr: {stderr_data}")

        except subprocess.TimeoutExpired:
            process.kill()
            print("ERROR: Timeout.")
        except Exception as e:
            print(f"ERROR: {e}")
        
        # Verify
        success = False
        reasons = []
        if final_json:
            success = True
            for k, v in scenario.expected_data_subset.items():
                if k not in final_json:
                    success = False
                    reasons.append(f"Missing key: {k}")
                elif scenario.strict and final_json[k] != v:
                    success = False
                    reasons.append(f"Value Mismatch {k}: expected {v}, got {final_json[k]}")
                elif not scenario.strict and str(v).lower() not in str(final_json[k]).lower():
                     # Loose match for things like string variations
                     # But for numbers: 
                     if isinstance(v, (int, float)) and final_json[k] != v:
                         success = False
                         reasons.append(f"Value Mismatch {k}: expected {v}, got {final_json[k]}")
        else:
            reasons.append("No final JSON produced")

        self.results.append({
            "name": scenario.name,
            "success": success,
            "reasons": reasons,
            "json": final_json
        })
        
        result_icon = "✅" if success else "❌"
        print(f"{result_icon} Result: {success}")
        if not success:
            print(f"   Reasons: {reasons}")
            print(f"   Captured JSON: {final_json}")


    def run_all(self):
        print(f"Starting execution of {len(self.scenarios)} scenarios...")
        start_t = time.time()
        for s in self.scenarios:
            self.run_scenario(s)
        end_t = time.time()
        
        # Report
        print("\n" + "="*60)
        print("FINAL REPORT")
        print("="*60)
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        print(f"Total Scenarios: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Time Taken: {end_t - start_t:.2f}s")
        print("="*60)
        
        for r in self.results:
            if not r['success']:
                print(f"FAILED: {r['name']} - {r['reasons']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
        print(f"Filtering scenarios by '{pattern}'")
        SCENARIOS = [s for s in SCENARIOS if pattern.lower() in s.name.lower()]
    
    runner = TestRunner(SCENARIOS)
    runner.run_all()
