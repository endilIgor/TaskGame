export type MissionType = "daily" | "weekly" | "long_term";
export type Difficulty = "easy" | "medium" | "hard" | "epic";
export type MissionStatus = "active" | "completed" | "archived";

export interface PlayerSummary {
  total_xp: number;
  gold: number;
  level: number;
  xp_into_level: number;
  xp_for_next_level: number;
  current_streak: number;
  best_streak: number;
}

export interface Mission {
  id: number;
  title: string;
  description: string | null;
  type: MissionType;
  difficulty: Difficulty;
  category: string | null;
  status: MissionStatus;
  start_date: string;
  target_date: string | null;
  repeat_days: number[] | null;
  progress_current: number;
  progress_target: number | null;
  created_at: string;
  updated_at: string;
}

export interface MissionCreate {
  title: string;
  type: MissionType;
  difficulty: Difficulty;
  description?: string;
  category?: string;
  start_date?: string;
  target_date?: string;
  progress_current?: number;
  progress_target?: number;
  repeat_days?: number[];
}

export interface MissionUpdate {
  title?: string;
  description?: string | null;
  type?: MissionType;
  difficulty?: Difficulty;
  category?: string | null;
  start_date?: string;
  target_date?: string | null;
  repeat_days?: number[] | null;
  progress_target?: number | null;
}

export interface BadgeStatus {
  id: number;
  code: string;
  name: string;
  description: string;
  condition_type: string;
  threshold: number;
  earned: boolean;
  earned_at: string | null;
}

export interface Reward {
  id: number;
  name: string;
  description: string | null;
  cost: number;
  status: string;
}

export interface RewardCreate {
  name: string;
  description?: string;
  cost: number;
}

export type RewardUpdate = Partial<RewardCreate>;

export interface RewardPurchase {
  id: number;
  reward_id: number;
  cost_paid: number;
  purchased_at: string;
}

export interface WeeklyReport {
  week_start: string;
  week_end: string;
  missions_completed: number;
  missions_failed: number;
  xp_gained: number;
  gold_gained: number;
  best_day: string | null;
  current_streak: number;
  best_streak: number;
  daily_completions: number[];
  top_categories: Array<{ category: string; completions: number }>;
  goals_completed: string[];
}

export interface BackupStatus {
  last_mysql_dump_at: string | null;
  last_mysql_dump_filename: string | null;
}

export interface BackupExport {
  missions: Mission[];
  mission_completions: unknown[];
  player_stats: unknown[];
  badges: unknown[];
  earned_badges: unknown[];
  rewards: Reward[];
  reward_purchases: unknown[];
  weekly_snapshots: unknown[];
}

export interface Dashboard {
  player: PlayerSummary;
  today: { completed: number; active: number; overdue: number };
  weekly: { missions_completed: number; xp_gained: number; gold_gained: number; best_day: string | null };
  upcoming_missions: Mission[];
  recent_badge: BadgeStatus | null;
}
