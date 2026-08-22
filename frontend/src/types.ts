export type ViewKey = "dashboard" | "missions" | "journal" | "goals" | "badges" | "rewards" | "reports";
export type MissionType = "daily" | "weekly" | "long_term";
export type Difficulty = "easy" | "medium" | "hard" | "epic";
export type MissionStatus = "active" | "completed" | "archived";
export type SkillType = "knowledge" | "strength" | "money" | "health" | "creativity" | "social";

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
  skill: string | null;
  status: MissionStatus;
  start_date: string;
  target_date: string | null;
  repeat_days: number[] | null;
  progress_current: number;
  progress_target: number | null;
  completion_count: number;
  total_xp_awarded: number;
  total_gold_awarded: number;
  completed_today: boolean;
  created_at: string;
  updated_at: string;
}

export interface MissionCreatePayload {
  title: string;
  type: MissionType;
  difficulty?: Difficulty;
  description?: string | null;
  category?: string | null;
  skill?: SkillType | null;
  start_date?: string;
  target_date?: string | null;
  progress_current?: number;
  progress_target?: number | null;
  repeat_days?: number[] | null;
}

export type MissionCreate = MissionCreatePayload;

export interface MissionUpdate {
  title?: string;
  description?: string | null;
  type?: MissionType;
  difficulty?: Difficulty;
  category?: string | null;
  skill?: SkillType | null;
  start_date?: string;
  target_date?: string | null;
  repeat_days?: number[] | null;
  progress_target?: number | null;
}

export interface MissionProgressPayload {
  amount: number;
}

export interface Goal extends Mission {
  progress_percent: number;
}

export interface MissionCompletion {
  id: number;
  mission_id: number;
  completed_at: string;
  xp_awarded: number;
  gold_awarded: number;
  streak_bonus_percent: number;
  note: string | null;
  mission_completion_count: number;
  mission_total_xp_awarded: number;
  mission_total_gold_awarded: number;
  unlocked_badges: BadgeStatus[];
}

export interface MissionCompletePayload {
  completed_on: string;
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

export interface RewardCreatePayload {
  name: string;
  description?: string | null;
  cost: number;
}

export type RewardCreate = RewardCreatePayload;
export type RewardUpdate = Partial<RewardCreatePayload>;

export interface RewardPurchase {
  id: number;
  reward_id: number;
  cost_paid: number;
  purchased_at: string;
}

export interface ReportDay {
  date: string;
  label: string;
  completions: number;
  xp_gained: number;
  gold_gained: number;
}

export interface ReportPeriod {
  period_type: "weekly" | "monthly";
  period_start: string;
  period_end: string;
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
  daily_activity: ReportDay[];
  top_categories: Array<{ category: string; completions: number }>;
  goals_completed: string[];
}

export type WeeklyReport = ReportPeriod;

export interface DashboardData {
  player: PlayerSummary;
  today: { completed: number; active: number; overdue: number };
  weekly: { missions_completed: number; xp_gained: number; gold_gained: number; best_day: string | null };
  upcoming_missions: Mission[];
  recent_badge: BadgeStatus | null;
}

export type Dashboard = DashboardData;

export interface JournalEntrySummary {
  id: number;
  title: string;
  entry_date: string;
  excerpt: string;
  mood: string | null;
  created_at: string;
  updated_at: string;
}

export interface JournalEntry extends JournalEntrySummary {
  content: string;
}

export interface JournalEntryCreatePayload {
  title?: string | null;
  entry_date: string;
  content: string;
  mood?: string | null;
}

export type JournalEntryUpdate = Partial<JournalEntryCreatePayload>;
