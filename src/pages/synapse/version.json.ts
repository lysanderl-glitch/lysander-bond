export const prerender = true;

export function GET() {
  const data = {
    version: "1.1.0",
    release_date: "2026-04-12",
    changelog_url: "https://github.com/lysanderl-glitch/synapse/blob/main/CHANGELOG.md",
    github_url: "https://github.com/lysanderl-glitch/synapse",
    upgrade_method: "git_pull",
    upgrade_command: "git pull origin main",
    min_version: "1.0.0",
    release_notes: "v1.1.0 adds evolution_engine agent for self-improvement loops, GAP analysis capability, and version management automation."
  };

  return new Response(JSON.stringify(data, null, 2), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600'
    }
  });
}
