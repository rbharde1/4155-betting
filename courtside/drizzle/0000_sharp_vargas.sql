CREATE TABLE `picks` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`game_id` text NOT NULL,
	`mode` text NOT NULL,
	`market` text NOT NULL,
	`side` integer NOT NULL,
	`label` text NOT NULL,
	`matchup` text NOT NULL,
	`odds` integer NOT NULL,
	`point` real,
	`stake_cents` integer NOT NULL,
	`profit_cents` integer NOT NULL,
	`result` text DEFAULT 'pending' NOT NULL,
	`source` text NOT NULL,
	`fetched_at` text NOT NULL,
	`start` text NOT NULL,
	`created_at` text NOT NULL,
	`settled_at` text,
	`score` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX `one_market_per_game` ON `picks` (`owner`,`mode`,`game_id`,`market`);--> statement-breakpoint
CREATE INDEX `picks_owner_mode` ON `picks` (`owner`,`mode`);--> statement-breakpoint
CREATE INDEX `picks_mode_game` ON `picks` (`mode`,`game_id`);