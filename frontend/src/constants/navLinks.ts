import { Home, Route, MapPin, Bot, User } from "lucide-react";
import { MobileNavItem } from "@/components/MobileNavMenu";

export const PRIMARY_NAV_LINKS: MobileNavItem[] = [
  { key: "home", label: "Home", href: "/homepage", Icon: Home },
  {
    key: "track",
    label: "Track",
    href: "/track_page/leaderboard",
    Icon: Route,
  },
  {
    key: "planning",
    label: "Planning",
    href: "/planning_page/showing_plan_page",
    Icon: MapPin,
  },
  { key: "ecobot", label: "Ecobot", href: "/ecobot_page", Icon: Bot },
  {
    key: "user",
    label: "User",
    href: "/user_page/main_page",
    Icon: User,
  },
];

export const MAP_NAV_LINKS: MobileNavItem[] = [
  { key: "home", label: "Home", href: "/homepage", Icon: Home },
  {
    key: "planning",
    label: "Planning",
    href: "/planning_page/showing_plan_page",
    Icon: MapPin,
  },
  { key: "ecobot", label: "Ecobot", href: "/ecobot_page", Icon: Bot },
  {
    key: "user",
    label: "User",
    href: "/user_page/main_page",
    Icon: User,
  },
];
