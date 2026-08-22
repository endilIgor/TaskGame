export type GameIconVariant = "shield" | "scroll" | "book" | "flag" | "medal" | "chart" | "spark" | "diamond" | "square" | "coin" | "triangle" | "cross" | "ring" | "calendar";

interface GameIconProps {
  variant: GameIconVariant;
  className?: string;
}

export function GameIcon({ variant, className = "" }: GameIconProps) {
  return <span className={`game-icon game-icon-${variant} ${className}`.trim()} aria-hidden="true" />;
}
