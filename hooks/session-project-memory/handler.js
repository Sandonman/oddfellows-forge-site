import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";

function resolveWorkspaceDir(event) {
  return (
    event?.context?.cfg?.workspace?.dir ||
    path.join(os.homedir(), ".openclaw", "workspace")
  );
}

function todayUtc() {
  return new Date().toISOString().slice(0, 10);
}

function sanitizeSlug(input) {
  return String(input || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

function sessionTail(sessionKey) {
  if (!sessionKey) return "";
  const parts = String(sessionKey).split(":");
  if (parts.length < 3) return "";
  return parts.slice(2).join(":");
}

async function readJsonObject(filePath) {
  try {
    const raw = await fs.readFile(filePath, "utf8");
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed)
      ? parsed
      : {};
  } catch {
    return {};
  }
}

function isMainControlChat(sessionKey) {
  const key = String(sessionKey || "");
  return (
    key === "agent:main:telegram:direct:8344173001" ||
    key === "telegram:direct:8344173001" ||
    key.endsWith(":telegram:direct:8344173001")
  );
}

async function ensureProjectsOverview(memoryDir, workspaceDir) {
  const overviewPath = path.join(memoryDir, "PROJECTS.md");
  try {
    await fs.access(overviewPath);
  } catch {
    const starter = `# Projects Overview\n\n## Active Projects\n- serenade-assisted-living-site\n- sky-high-dining-site\n- oddfellows-forge-site\n- serenade-assisted-living-document-system\n\n## Routing Notes\n- Group chats are mapped per chat ID in memory/project-routing.json\n- Main direct chat is control-plane (not project-bound)\n\n## How to Use This Chat\n- Use this chat for project setup, cross-project questions, and non-project requests\n- For project-specific execution, use the mapped group chat for that project\n`;
    await fs.mkdir(memoryDir, { recursive: true });
    await fs.writeFile(overviewPath, starter, "utf8");
  }
  return path.relative(workspaceDir, overviewPath);
}

async function resolveProjectSlug({ memoryDir, sessionKey }) {
  const routingPath = path.join(memoryDir, "project-routing.json");
  const pointerPath = path.join(memoryDir, ".current-project");
  const routing = await readJsonObject(routingPath);

  const direct = sanitizeSlug(routing[sessionKey]);
  if (direct) return direct;

  const tail = sessionTail(sessionKey);
  const byTail = sanitizeSlug(routing[tail]);
  if (byTail) return byTail;

  // optional default key in routing file
  const fallback = sanitizeSlug(routing.default);
  if (fallback) return fallback;

  try {
    const pointer = sanitizeSlug(await fs.readFile(pointerPath, "utf8"));
    return pointer;
  } catch {
    return "";
  }
}

export default async function sessionProjectMemory(event) {
  if (event?.type !== "session" || event?.action !== "start") return;

  const workspaceDir = resolveWorkspaceDir(event);
  const memoryDir = path.join(workspaceDir, "memory");
  const sessionKey = String(event?.sessionKey || "");

  event.messages ??= [];

  if (isMainControlChat(sessionKey)) {
    const relOverview = await ensureProjectsOverview(memoryDir, workspaceDir);
    event.messages.push(
      `Session restarted. This is the main control chat (not project-bound). Read ${relOverview} for cross-project context.`
    );
    return;
  }

  const projectSlug = await resolveProjectSlug({ memoryDir, sessionKey });
  if (!projectSlug) return;

  const date = todayUtc();
  const projectDir = path.join(memoryDir, projectSlug);
  const dailyPath = path.join(projectDir, `${date}.md`);

  const activeProjectPath = path.join(workspaceDir, "projects", projectSlug);
  const dormantProjectPath = path.join(
    workspaceDir,
    "archive",
    "projects",
    "dormant",
    projectSlug
  );
  const completedProjectPath = path.join(
    workspaceDir,
    "archive",
    "projects",
    "completed",
    projectSlug
  );

  let resolvedProjectPath = activeProjectPath;
  try {
    await fs.access(activeProjectPath);
  } catch {
    try {
      await fs.access(dormantProjectPath);
      resolvedProjectPath = dormantProjectPath;
    } catch {
      try {
        await fs.access(completedProjectPath);
        resolvedProjectPath = completedProjectPath;
      } catch {
        resolvedProjectPath = activeProjectPath;
      }
    }
  }

  await fs.mkdir(projectDir, { recursive: true });

  try {
    await fs.access(dailyPath);
  } catch {
    const starter = `# ${projectSlug} — ${date}\n\n## Goal\n- \n\n## Last Completed\n- \n\n## Next Step\n- \n\n## Notes\n- \n`;
    await fs.writeFile(dailyPath, starter, "utf8");
  }

  const relDaily = path.relative(workspaceDir, dailyPath);
  const relProjectPath = path.relative(workspaceDir, resolvedProjectPath);
  event.messages.push(
    `Session restarted. Read ${relDaily} for context, then continue project in ${relProjectPath}. Keep SUMMARY.md concise and updated at milestones. Do not create new project folders from group chats; request new project creation in main control chat.`
  );
}
