import type { HeroClass, SkillType } from "../types";

export interface HeroClassInfo {
  id: HeroClass;
  label: string;
  tagline: string;
  description: string;
  focusSkills: SkillType[];
  accent: "red" | "violet" | "emerald" | "blue";
  sprite: string;
}

export const HERO_CLASSES: HeroClassInfo[] = [
  {
    id: "warrior",
    label: "Guerreiro",
    tagline: "Disciplina, treino e execução.",
    description: "Constrói força de vontade através de ação e repetição. Ideal para tarefas físicas e hábitos de treino.",
    focusSkills: ["strength", "health"],
    accent: "red",
    sprite: "/assets/heroes/warrior.svg",
  },
  {
    id: "mage",
    label: "Mago",
    tagline: "Estudo, foco profundo e criação.",
    description: "Canaliza energia para aprender e criar. Ideal para quem quer evoluir conhecimento e criatividade.",
    focusSkills: ["knowledge", "creativity"],
    accent: "violet",
    sprite: "/assets/heroes/mage.svg",
  },
  {
    id: "archer",
    label: "Arqueiro",
    tagline: "Precisão, consistência e hábitos diários.",
    description: "Vence pela constância e pelo planejamento. Ideal para quem busca rotina, foco e organização financeira.",
    focusSkills: ["knowledge", "health", "money"],
    accent: "emerald",
    sprite: "/assets/heroes/archer.svg",
  },
  {
    id: "guardian",
    label: "Guardião",
    tagline: "Saúde, família e estabilidade.",
    description: "Protege o que importa: corpo, casa e relações. Ideal para quem quer equilibrar saúde e vida social.",
    focusSkills: ["health", "social"],
    accent: "blue",
    sprite: "/assets/heroes/guardian.svg",
  },
];

export function heroClassById(id: HeroClass): HeroClassInfo {
  const found = HERO_CLASSES.find((heroClass) => heroClass.id === id);
  if (!found) throw new Error(`Unknown hero class: ${id}`);
  return found;
}
