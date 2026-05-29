export const prerender = true;

export function GET() {
  const data = {
    version: "1.0.0",
    release_date: "2026-04-12",
    changelog_url: "https://github.com/lysanderl-glitch/synapse/blob/main/CHANGELOG.md",
    github_url: "https://github.com/lysanderl-glitch/synapse",
    upgrade_method: "git_pull",
    upgrade_command: "git pull origin main",
    min_version: "1.0.0",
    release_notes: "v1.0.0 — First public release. 55 active core agents across 12 teams (canonical as of 2026-05-28, source: agent-CEO/config/organization.yaml deduped union of teams.*.members), CEO Guard hooks, Harness Engineering methodology."
  };

  return new Response(JSON.stringify(data, null, 2), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600'
    }
  });
}
