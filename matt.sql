-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               PostgreSQL 18.1 on x86_64-windows, compiled by msvc-19.44.35219, 64-bit
-- Server OS:                    
-- HeidiSQL Version:             12.1.0.6537
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES  */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Dumping structure for table public.accounts_metabolicprofile
CREATE TABLE IF NOT EXISTS "accounts_metabolicprofile" (
	"id" BIGINT NOT NULL,
	"bmr" NUMERIC(10,2) NULL DEFAULT NULL,
	"tdee" NUMERIC(10,2) NULL DEFAULT NULL,
	"daily_calorie_target" NUMERIC(10,2) NULL DEFAULT NULL,
	"protein_g" DOUBLE PRECISION NULL DEFAULT NULL,
	"carbs_g" DOUBLE PRECISION NULL DEFAULT NULL,
	"fats_g" DOUBLE PRECISION NULL DEFAULT NULL,
	"estimated_days_to_goal" DOUBLE PRECISION NULL DEFAULT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	UNIQUE INDEX "accounts_metabolicprofile_user_id_key" ("user_id"),
	CONSTRAINT "accounts_metabolicprofile_user_id_2ab6b51e_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.accounts_onboardingprofile
CREATE TABLE IF NOT EXISTS "accounts_onboardingprofile" (
	"id" BIGINT NOT NULL,
	"gender" VARCHAR(10) NULL DEFAULT NULL,
	"date_of_birth" DATE NULL DEFAULT NULL,
	"image" VARCHAR(100) NULL DEFAULT NULL,
	"current_height" NUMERIC(5,2) NULL DEFAULT NULL,
	"current_height_unit" VARCHAR(5) NULL DEFAULT NULL,
	"current_weight" NUMERIC(6,2) NULL DEFAULT NULL,
	"current_weight_unit" VARCHAR(5) NULL DEFAULT NULL,
	"target_weight" NUMERIC(6,2) NULL DEFAULT NULL,
	"target_weight_unit" VARCHAR(5) NULL DEFAULT NULL,
	"goal" VARCHAR(15) NULL DEFAULT NULL,
	"target_speed" VARCHAR(10) NULL DEFAULT NULL,
	"activity_level" VARCHAR(20) NULL DEFAULT NULL,
	"vegan" BOOLEAN NOT NULL,
	"dairy_free" BOOLEAN NOT NULL,
	"gluten_free" BOOLEAN NOT NULL,
	"nut_free" BOOLEAN NOT NULL,
	"pescatarian" BOOLEAN NOT NULL,
	"user_id" BIGINT NOT NULL,
	"last_message" TEXT NOT NULL,
	PRIMARY KEY ("id"),
	UNIQUE INDEX "accounts_onboardingprofile_user_id_key" ("user_id"),
	CONSTRAINT "accounts_onboardingprofile_user_id_7121128a_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.accounts_user
CREATE TABLE IF NOT EXISTS "accounts_user" (
	"id" BIGINT NOT NULL,
	"password" VARCHAR(128) NOT NULL,
	"name" VARCHAR(255) NOT NULL,
	"email" VARCHAR(254) NOT NULL,
	"phone" VARCHAR(15) NOT NULL,
	"role" VARCHAR(8) NOT NULL,
	"device_token" VARCHAR(255) NULL DEFAULT NULL,
	"is_active" BOOLEAN NOT NULL,
	"is_staff" BOOLEAN NOT NULL,
	"is_superuser" BOOLEAN NOT NULL,
	"date_joined" TIMESTAMPTZ NOT NULL,
	"last_login" TIMESTAMPTZ NULL DEFAULT NULL,
	"otp" VARCHAR(6) NULL DEFAULT NULL,
	"otp_expiry" TIMESTAMPTZ NULL DEFAULT NULL,
	"auth_provider" VARCHAR(20) NOT NULL,
	"social_id" VARCHAR(500) NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	UNIQUE INDEX "accounts_user_email_key" ("email"),
	UNIQUE INDEX "accounts_user_phone_key" ("phone"),
	INDEX "accounts_user_email_b2644a56_like" ("email"),
	INDEX "accounts_user_phone_c603acdd_like" ("phone"),
	UNIQUE INDEX "accounts_user_social_id_key" ("social_id"),
	INDEX "accounts_u_social_idx" ("social_id"),
	INDEX "accounts_user_social_id_1153ef09_like" ("social_id")
);

-- Data exporting was unselected.

-- Dumping structure for table public.accounts_useractivity
CREATE TABLE IF NOT EXISTS "accounts_useractivity" (
	"id" BIGINT NOT NULL,
	"title" VARCHAR(255) NOT NULL,
	"description" TEXT NULL DEFAULT NULL,
	"activity_type" VARCHAR(20) NOT NULL,
	"metadata" JSONB NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "accounts_useractivity_created_at_19accfdb" ("created_at"),
	INDEX "accounts_useractivity_user_id_4dd2bb87" ("user_id"),
	CONSTRAINT "accounts_useractivity_user_id_4dd2bb87_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.chats_chatmessage
CREATE TABLE IF NOT EXISTS "chats_chatmessage" (
	"id" BIGINT NOT NULL,
	"content" TEXT NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NULL DEFAULT NULL,
	"role" VARCHAR(20) NOT NULL,
	"session_id" BIGINT NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	INDEX "chats_chatmessage_user_id_79aca0cf" ("user_id"),
	INDEX "chats_chatmessage_session_id_ff055b28" ("session_id"),
	CONSTRAINT "chats_chatmessage_session_id_ff055b28_fk_chats_chatsession_id" FOREIGN KEY ("session_id") REFERENCES "chats_chatsession" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "chats_chatmessage_user_id_79aca0cf_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.chats_chatsession
CREATE TABLE IF NOT EXISTS "chats_chatsession" (
	"id" BIGINT NOT NULL,
	"session" UUID NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	"name" VARCHAR(255) NOT NULL,
	PRIMARY KEY ("id"),
	UNIQUE INDEX "chats_chatsession_session_key" ("session"),
	INDEX "chats_chatsession_user_id_93b36471" ("user_id"),
	CONSTRAINT "chats_chatsession_user_id_93b36471_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.chats_onboardingconversation
CREATE TABLE IF NOT EXISTS "chats_onboardingconversation" (
	"id" BIGINT NOT NULL,
	"role" VARCHAR(20) NOT NULL,
	"content" TEXT NOT NULL,
	"collected_data" JSONB NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "chats_onboardingconversation_user_id_2f18d54b" ("user_id"),
	CONSTRAINT "chats_onboardingconv_user_id_2f18d54b_fk_accounts_" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.cores_helpsupport
CREATE TABLE IF NOT EXISTS "cores_helpsupport" (
	"id" BIGINT NOT NULL,
	"description" TEXT NOT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "cores_helpsupport_user_id_da45e95f" ("user_id"),
	CONSTRAINT "cores_helpsupport_user_id_da45e95f_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.cores_privacypolicy
CREATE TABLE IF NOT EXISTS "cores_privacypolicy" (
	"id" BIGINT NOT NULL,
	"content" TEXT NOT NULL,
	PRIMARY KEY ("id")
);

-- Data exporting was unselected.

-- Dumping structure for table public.cores_termsconditions
CREATE TABLE IF NOT EXISTS "cores_termsconditions" (
	"id" BIGINT NOT NULL,
	"content" TEXT NOT NULL,
	PRIMARY KEY ("id")
);


-- Data exporting was unselected.

-- Dumping structure for table public.meals_dailymeals
CREATE TABLE IF NOT EXISTS "meals_dailymeals" (
	"id" BIGINT NOT NULL,
	"meal_type" VARCHAR(20) NULL DEFAULT NULL,
	"name" VARCHAR(255) NOT NULL,
	"source" VARCHAR(20) NOT NULL,
	"servings" INTEGER NULL DEFAULT NULL,
	"prepare_time" VARCHAR(50) NULL DEFAULT NULL,
	"nutrients" JSONB NULL DEFAULT NULL,
	"tags" JSONB NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	"meal_plan_id" BIGINT NOT NULL,
	"meal_date" DATE NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "meals_dailymeals_user_id_72165328" ("user_id"),
	INDEX "meals_dailymeals_meal_plan_id_0b3d99cc" ("meal_plan_id"),
	UNIQUE INDEX "meals_dailymeals_user_id_meal_type_meal_date_bc0fef6c_uniq" ("user_id", "meal_type", "meal_date"),
	CONSTRAINT "meals_dailymeals_meal_plan_id_0b3d99cc_fk_meals_mealplan_id" FOREIGN KEY ("meal_plan_id") REFERENCES "meals_mealplan" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "meals_dailymeals_user_id_72165328_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "meals_dailymeals_servings_check" CHECK ((servings >= 0))
);

-- Data exporting was unselected.

-- Dumping structure for table public.meals_foodingredient
CREATE TABLE IF NOT EXISTS "meals_foodingredient" (
	"id" BIGINT NOT NULL,
	"name" VARCHAR(255) NOT NULL,
	"quantity" VARCHAR(50) NULL DEFAULT NULL,
	"unit" VARCHAR(20) NULL DEFAULT NULL,
	"nutrients" JSONB NULL DEFAULT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"item_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "meals_foodingredient_item_id_3395f28d" ("item_id"),
	CONSTRAINT "meals_foodingredient_item_id_3395f28d_fk_meals_fooditem_id" FOREIGN KEY ("item_id") REFERENCES "meals_fooditem" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.meals_fooditem
CREATE TABLE IF NOT EXISTS "meals_fooditem" (
	"id" BIGINT NOT NULL,
	"name" VARCHAR(255) NOT NULL,
	"description" TEXT NULL DEFAULT NULL,
	"quantity" VARCHAR(50) NULL DEFAULT NULL,
	"unit" VARCHAR(20) NULL DEFAULT NULL,
	"nutrients" JSONB NULL DEFAULT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	"meal_id" BIGINT NULL DEFAULT NULL,
	"recipe_id" BIGINT NULL DEFAULT NULL,
	"saved_meal_id" BIGINT NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	INDEX "meals_fooditem_meal_id_da91dc26" ("meal_id"),
	INDEX "meals_fooditem_recipe_id_3814be51" ("recipe_id"),
	INDEX "meals_fooditem_saved_meal_id_34e6471f" ("saved_meal_id"),
	CONSTRAINT "meals_fooditem_meal_id_da91dc26_fk_meals_dailymeals_id" FOREIGN KEY ("meal_id") REFERENCES "meals_dailymeals" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "meals_fooditem_recipe_id_3814be51_fk_pantry_recipe_id" FOREIGN KEY ("recipe_id") REFERENCES "pantry_recipe" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "meals_fooditem_saved_meal_id_34e6471f_fk_meals_savedmeal_id" FOREIGN KEY ("saved_meal_id") REFERENCES "meals_savedmeal" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.meals_logmeals
CREATE TABLE IF NOT EXISTS "meals_logmeals" (
	"id" BIGINT NOT NULL,
	"meal_type" VARCHAR(20) NULL DEFAULT NULL,
	"name" VARCHAR(255) NOT NULL,
	"prepare_time" VARCHAR(50) NULL DEFAULT NULL,
	"nutrients" JSONB NULL DEFAULT NULL,
	"tags" JSONB NOT NULL,
	"status" VARCHAR(20) NOT NULL,
	"meal_date" DATE NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	"meal_plan_id" BIGINT NULL DEFAULT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "meals_logmeals_meal_plan_id_1b0cbd1b" ("meal_plan_id"),
	INDEX "meals_logmeals_user_id_610f086b" ("user_id"),
	CONSTRAINT "meals_logmeals_meal_plan_id_1b0cbd1b_fk_meals_mealplan_id" FOREIGN KEY ("meal_plan_id") REFERENCES "meals_mealplan" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "meals_logmeals_user_id_610f086b_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.meals_mealplan
CREATE TABLE IF NOT EXISTS "meals_mealplan" (
	"id" BIGINT NOT NULL,
	"start_date" DATE NOT NULL,
	"end_date" DATE NOT NULL,
	"total_days" INTEGER NOT NULL,
	"is_active" BOOLEAN NOT NULL,
	"is_completed" BOOLEAN NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "meals_mealplan_user_id_fcd719ea" ("user_id"),
	CONSTRAINT "meals_mealplan_user_id_fcd719ea_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "meals_mealplan_total_days_check" CHECK ((total_days >= 0))
);

-- Data exporting was unselected.

-- Dumping structure for table public.meals_savedmeal
CREATE TABLE IF NOT EXISTS "meals_savedmeal" (
	"id" BIGINT NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	"meal_type" VARCHAR(20) NULL DEFAULT NULL,
	"nutrients" JSONB NULL DEFAULT NULL,
	"prepare_time" VARCHAR(50) NULL DEFAULT NULL,
	"servings" INTEGER NULL DEFAULT NULL,
	"source" VARCHAR(20) NOT NULL,
	"tags" JSONB NOT NULL,
	"name" VARCHAR(255) NOT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "meals_savedmeal_user_id_63edfa69" ("user_id"),
	CONSTRAINT "meals_savedmeal_user_id_63edfa69_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "meals_savedmeal_servings_check" CHECK ((servings >= 0))
);

-- Data exporting was unselected.

-- Dumping structure for table public.pantry_pantryitem
CREATE TABLE IF NOT EXISTS "pantry_pantryitem" (
	"id" BIGINT NOT NULL,
	"item_name" VARCHAR(255) NOT NULL,
	"quantity" NUMERIC(10,2) NULL DEFAULT NULL,
	"unit_price" NUMERIC(10,2) NULL DEFAULT NULL,
	"price" NUMERIC(10,2) NULL DEFAULT NULL,
	"unit" VARCHAR(50) NOT NULL,
	"quantity_type" VARCHAR(20) NULL DEFAULT NULL,
	"nutrients" JSONB NULL DEFAULT NULL,
	"low_inventory_threshold" DOUBLE PRECISION NOT NULL,
	"expiration_date" DATE NULL DEFAULT NULL,
	"notes" TEXT NULL DEFAULT NULL,
	"last_updated" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "pantry_pantryitem_user_id_f5136fca" ("user_id"),
	CONSTRAINT "pantry_pantryitem_user_id_f5136fca_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.pantry_pantryitemhistory
CREATE TABLE IF NOT EXISTS "pantry_pantryitemhistory" (
	"id" BIGINT NOT NULL,
	"action" VARCHAR(10) NOT NULL,
	"quantity_changed" DOUBLE PRECISION NULL DEFAULT NULL,
	"old_quantity" DOUBLE PRECISION NULL DEFAULT NULL,
	"new_quantity" DOUBLE PRECISION NULL DEFAULT NULL,
	"date" TIMESTAMPTZ NOT NULL,
	"old_notes" TEXT NULL DEFAULT NULL,
	"new_notes" TEXT NULL DEFAULT NULL,
	"pantry_item_id" BIGINT NOT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "pantry_pantryitemhistory_pantry_item_id_69eb86e0" ("pantry_item_id"),
	INDEX "pantry_pantryitemhistory_user_id_57a671a7" ("user_id"),
	CONSTRAINT "pantry_pantryitemhis_pantry_item_id_69eb86e0_fk_pantry_pa" FOREIGN KEY ("pantry_item_id") REFERENCES "pantry_pantryitem" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "pantry_pantryitemhistory_user_id_57a671a7_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.pantry_recipe
CREATE TABLE IF NOT EXISTS "pantry_recipe" (
	"id" BIGINT NOT NULL,
	"name" VARCHAR(255) NOT NULL,
	"servings" INTEGER NULL DEFAULT NULL,
	"prepare_time" VARCHAR(50) NULL DEFAULT NULL,
	"nutrients" JSONB NULL DEFAULT NULL,
	"tags" JSONB NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	"meal_type" VARCHAR(20) NULL DEFAULT NULL,
	"source" VARCHAR(20) NOT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "pantry_recipe_user_id_742e14eb" ("user_id"),
	CONSTRAINT "pantry_recipe_user_id_742e14eb_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "pantry_recipe_servings_check" CHECK ((servings >= 0))
);

-- Data exporting was unselected.

-- Dumping structure for table public.pantry_recipeprocess
CREATE TABLE IF NOT EXISTS "pantry_recipeprocess" (
	"id" BIGINT NOT NULL,
	"process" TEXT NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	"recipe_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	UNIQUE INDEX "pantry_recipeprocess_recipe_id_key" ("recipe_id"),
	CONSTRAINT "pantry_recipeprocess_recipe_id_c9efd422_fk_pantry_recipe_id" FOREIGN KEY ("recipe_id") REFERENCES "pantry_recipe" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.progress_progressentry
CREATE TABLE IF NOT EXISTS "progress_progressentry" (
	"id" BIGINT NOT NULL,
	"date" DATE NOT NULL,
	"weight_kg" DOUBLE PRECISION NOT NULL,
	"body_fat_percentage" DOUBLE PRECISION NOT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "progress_progressentry_user_id_d0db6855" ("user_id"),
	CONSTRAINT "progress_progressentry_user_id_d0db6855_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.shopping_shoppingitem
CREATE TABLE IF NOT EXISTS "shopping_shoppingitem" (
	"id" BIGINT NOT NULL,
	"name" VARCHAR(255) NOT NULL,
	"group_name" VARCHAR(255) NULL DEFAULT NULL,
	"quantity" DOUBLE PRECISION NOT NULL,
	"unit" VARCHAR(50) NOT NULL,
	"bought" BOOLEAN NOT NULL,
	"price" NUMERIC(10,2) NULL DEFAULT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"user_id" BIGINT NOT NULL,
	"nutrients" JSONB NULL DEFAULT NULL,
	"updated_at" TIMESTAMPTZ NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "shopping_shoppingitem_user_id_97ed043d" ("user_id"),
	CONSTRAINT "shopping_shoppingitem_user_id_97ed043d_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.shopping_shoppingitemhistory
CREATE TABLE IF NOT EXISTS "shopping_shoppingitemhistory" (
	"id" BIGINT NOT NULL,
	"action" VARCHAR(20) NOT NULL,
	"quantity_changed" DOUBLE PRECISION NULL DEFAULT NULL,
	"old_quantity" DOUBLE PRECISION NULL DEFAULT NULL,
	"new_quantity" DOUBLE PRECISION NULL DEFAULT NULL,
	"date" TIMESTAMPTZ NOT NULL,
	"shopping_item_id" BIGINT NOT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	INDEX "shopping_shoppingitemhistory_shopping_item_id_12bc68aa" ("shopping_item_id"),
	INDEX "shopping_shoppingitemhistory_user_id_2d3a8c4a" ("user_id"),
	CONSTRAINT "shopping_shoppingite_shopping_item_id_12bc68aa_fk_shopping_" FOREIGN KEY ("shopping_item_id") REFERENCES "shopping_shoppingitem" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "shopping_shoppingite_user_id_2d3a8c4a_fk_accounts_" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.subscriptions_plan
CREATE TABLE IF NOT EXISTS "subscriptions_plan" (
	"id" BIGINT NOT NULL,
	"name" VARCHAR(100) NOT NULL,
	"tier" SMALLINT NOT NULL,
	"interval" VARCHAR(20) NOT NULL,
	"trial_days" INTEGER NOT NULL,
	"unit_amount" INTEGER NOT NULL,
	"stripe_price_id" VARCHAR(255) NOT NULL,
	"is_active" BOOLEAN NOT NULL,
	"is_recommended" BOOLEAN NOT NULL,
	PRIMARY KEY ("id"),
	UNIQUE INDEX "subscriptions_plan_stripe_price_id_key" ("stripe_price_id"),
	INDEX "subscriptions_plan_stripe_price_id_281c3dca_like" ("stripe_price_id"),
	CONSTRAINT "subscriptions_plan_tier_check" CHECK ((tier >= 0)),
	CONSTRAINT "subscriptions_plan_trial_days_check" CHECK ((trial_days >= 0)),
	CONSTRAINT "subscriptions_plan_unit_amount_check" CHECK ((unit_amount >= 0))
);

-- Data exporting was unselected.

-- Dumping structure for table public.subscriptions_subscription
CREATE TABLE IF NOT EXISTS "subscriptions_subscription" (
	"id" BIGINT NOT NULL,
	"stripe_subscription_id" VARCHAR(255) NOT NULL,
	"stripe_customer_id" VARCHAR(255) NULL DEFAULT NULL,
	"status" VARCHAR(20) NOT NULL,
	"current_period_end" TIMESTAMPTZ NULL DEFAULT NULL,
	"trial_start" TIMESTAMPTZ NULL DEFAULT NULL,
	"trial_end" TIMESTAMPTZ NULL DEFAULT NULL,
	"plan_id" BIGINT NULL DEFAULT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	UNIQUE INDEX "subscriptions_subscription_stripe_subscription_id_key" ("stripe_subscription_id"),
	UNIQUE INDEX "subscriptions_subscription_stripe_customer_id_key" ("stripe_customer_id"),
	UNIQUE INDEX "subscriptions_subscription_user_id_key" ("user_id"),
	INDEX "subscriptions_subscription_stripe_subscription_id_17762401_like" ("stripe_subscription_id"),
	INDEX "subscriptions_subscription_stripe_customer_id_30c44188_like" ("stripe_customer_id"),
	INDEX "subscriptions_subscription_plan_id_2c895107" ("plan_id"),
	CONSTRAINT "subscriptions_subscr_plan_id_2c895107_fk_subscript" FOREIGN KEY ("plan_id") REFERENCES "subscriptions_plan" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "subscriptions_subscription_user_id_a353e93d_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Data exporting was unselected.

-- Dumping structure for table public.subscriptions_transaction
CREATE TABLE IF NOT EXISTS "subscriptions_transaction" (
	"id" BIGINT NOT NULL,
	"stripe_invoice_id" VARCHAR(255) NOT NULL,
	"amount" INTEGER NOT NULL,
	"status" VARCHAR(20) NOT NULL,
	"created_at" TIMESTAMPTZ NOT NULL,
	"subscription_id" BIGINT NULL DEFAULT NULL,
	"user_id" BIGINT NOT NULL,
	PRIMARY KEY ("id"),
	UNIQUE INDEX "subscriptions_transaction_stripe_invoice_id_key" ("stripe_invoice_id"),
	INDEX "subscriptions_transaction_stripe_invoice_id_cc236804_like" ("stripe_invoice_id"),
	INDEX "subscriptions_transaction_subscription_id_5f7ab89a" ("subscription_id"),
	INDEX "subscriptions_transaction_user_id_309bf016" ("user_id"),
	CONSTRAINT "subscriptions_transa_subscription_id_5f7ab89a_fk_subscript" FOREIGN KEY ("subscription_id") REFERENCES "subscriptions_subscription" ("id") ON UPDATE NO ACTION ON DELETE CASCADE,
	CONSTRAINT "subscriptions_transaction_user_id_309bf016_fk_accounts_user_id" FOREIGN KEY ("user_id") REFERENCES "accounts_user" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "subscriptions_transaction_amount_check" CHECK ((amount >= 0))
);

-- Data exporting was unselected.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
