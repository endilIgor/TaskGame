interface ViewProps {
  hidden?: boolean;
}

export function BackupView({ hidden }: ViewProps) {
  return <section hidden={hidden} />;
}
