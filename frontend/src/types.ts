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
  type: string;
  difficulty: string;
  category: string | null;
  status: string;
  start_date: string;
  target_date: string | null;
  repeat_days: number[] | null;
  progress_current: number;
  progress_target: number | null;
  created_at: string;
  updated_at: string;
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

export interface Dashboard {
  player: PlayerSummary;
  today: { completed: number; active: number; overdue: number };
  weekly: { missions_completed: number; xp_gained: number; gold_gained: number; best_day: string | null };
  upcoming_missions: Mission[];
  recent_badge: BadgeStatus | null;
}
