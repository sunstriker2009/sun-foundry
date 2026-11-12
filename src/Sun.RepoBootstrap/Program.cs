using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

var mode = Arg("--mode") ?? "audit";
var repo = Arg("--repo") ?? throw new ArgumentException("--repo owner/name required");
var checks = (Arg("--checks") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
var confirmation = Arg("--confirm") ?? "";
if (!new[] { "audit", "plan", "apply", "verify" }.Contains(mode)) throw new ArgumentException("Unsupported mode");
if (!System.Text.RegularExpressions.Regex.IsMatch(repo, @"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")) throw new ArgumentException("Invalid repo");
var token = Environment.GetEnvironmentVariable("GH_TOKEN") ?? throw new InvalidOperationException("GH_TOKEN required (fine-grained token with repository Administration write for apply; read for audit)");
using var http = new HttpClient { BaseAddress = new Uri("https://api.github.com/") };
http.DefaultRequestHeaders.UserAgent.ParseAdd("sun-repo-bootstrap/0.1");
http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github+json"));
http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
http.DefaultRequestHeaders.Add("X-GitHub-Api-Version", "2022-11-28");

async Task<JsonNode?> Api(string method, string path, object? payload = null)
{
    using var request = new HttpRequestMessage(new HttpMethod(method), path);
    if (payload is not null) request.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
    using var response = await http.SendAsync(request);
    var body = await response.Content.ReadAsStringAsync();
    if (!response.IsSuccessStatusCode) throw new HttpRequestException($"GitHub {method} {path}: {(int)response.StatusCode} {body}", null, response.StatusCode);
    return string.IsNullOrWhiteSpace(body) ? null : JsonNode.Parse(body);
}

var info = await Api("GET", $"repos/{repo}") ?? throw new InvalidOperationException("Repository not found");
var main = info["default_branch"]?.GetValue<string>() ?? "main";
var settings = new Dictionary<string, object> {
    ["allow_squash_merge"] = true, ["allow_merge_commit"] = false, ["allow_rebase_merge"] = false,
    ["allow_auto_merge"] = true, ["delete_branch_on_merge"] = true,
    ["squash_merge_commit_title"] = "PR_TITLE", ["squash_merge_commit_message"] = "PR_BODY"
};
var diffs = settings.Where(kv => info[kv.Key]?.ToJsonString() != JsonSerializer.Serialize(kv.Value))
    .Select(kv => $"{kv.Key}: {info[kv.Key]?.ToJsonString() ?? "(unknown)"} -> {JsonSerializer.Serialize(kv.Value)}").ToArray();
var rules = await Api("GET", $"repos/{repo}/rulesets?includes_parents=false") as JsonArray ?? new JsonArray();
var existing = rules.FirstOrDefault(x => x?["name"]?.GetValue<string>() == "SUN Main Protection");
var rulePresent = existing is not null;
Console.WriteLine($"SUN Git Policy v1.0 | {repo} | default branch: {main} | mode: {mode}");
foreach (var diff in diffs) Console.WriteLine($"SETTING DRIFT: {diff}");
Console.WriteLine(rulePresent ? "RULESET: SUN Main Protection exists (contents must be verified)" : "RULESET MISSING: SUN Main Protection");
if (checks.Length == 0) Console.WriteLine("WARNING: exact required checks are needed for apply and verify.");
if (checks.Distinct(StringComparer.Ordinal).Count() != checks.Length) throw new ArgumentException("Duplicate required check names");
if (mode == "verify" && checks.Length == 0) throw new ArgumentException("Verify requires --checks for exact membership comparison");
if (mode == "plan" || mode == "audit") { Environment.ExitCode = mode == "audit" && (diffs.Length > 0 || !rulePresent) ? 2 : 0; return; }
if (mode == "apply")
{
    if (confirmation != repo) throw new InvalidOperationException("Apply requires --confirm equal to target repository");
    if (checks.Length == 0) throw new InvalidOperationException("Apply requires --checks with exact CI check names");
    if (main != "main") throw new InvalidOperationException("Expected default branch main; review repository before applying");
    // Do not overwrite existing rulesets: human review required to avoid weakening established controls.
    if (rulePresent) throw new InvalidOperationException("SUN Main Protection already exists. Refusing to overwrite: audit existing ruleset manually before applying.");
    // GitHub's check names must already exist; validate against check runs for latest main commit.
    var sha = info["default_branch"] is null ? null : (await Api("GET", $"repos/{repo}/branches/{main}"))?["commit"]?["sha"]?.GetValue<string>();
    var runs = await Api("GET", $"repos/{repo}/commits/{sha}/check-runs?per_page=100");
    var known = (runs?["check_runs"] as JsonArray ?? new JsonArray()).Select(x => x?["name"]?.GetValue<string>()).Where(x => x is not null).ToHashSet();
    // PR-only checks do not run on main; discover them on open pull-request heads.
    var prs = await Api("GET", $"repos/{repo}/pulls?state=open&per_page=100") as JsonArray ?? new JsonArray();
    foreach (var item in prs)
    {
        var headSha = item?["head"]?["sha"]?.GetValue<string>();
        if (string.IsNullOrEmpty(headSha)) continue;
        var prRuns = await Api("GET", $"repos/{repo}/commits/{headSha}/check-runs?per_page=100");
        foreach (var run in prRuns?["check_runs"] as JsonArray ?? new JsonArray())
        {
            var name = run?["name"]?.GetValue<string>();
            if (!string.IsNullOrEmpty(name)) known.Add(name);
        }
    }
    var missing = checks.Where(x => !known.Contains(x)).ToArray();
    if (missing.Length > 0) throw new InvalidOperationException("Check names not found on main or open PR heads: " + string.Join(", ", missing) + ". Run CI on main first.");
    // Ruleset created before modifying merge settings, so failure cannot leave merge-method changes without branch protection.
    var ruleset = new {
        name = "SUN Main Protection", target = "branch", enforcement = "active",
        conditions = new { ref_name = new { include = new[] { "refs/heads/main" }, exclude = Array.Empty<string>() } },
        bypass_actors = Array.Empty<object>(),
        rules = new object[] {
            new { type = "deletion" }, new { type = "non_fast_forward" },
            new { type = "pull_request", parameters = new { required_approving_review_count = 0, dismiss_stale_reviews_on_push = true, require_code_owner_review = false, require_last_push_approval = false, required_review_thread_resolution = true } },
            new { type = "required_status_checks", parameters = new { strict_required_status_checks_policy = true, do_not_enforce_on_create = false, required_status_checks = checks.Select(x => new { context = x }).ToArray() } }
        }
    };
    await Api("POST", $"repos/{repo}/rulesets", ruleset);
    Console.WriteLine("Created active SUN Main Protection ruleset.");
    await Api("PATCH", $"repos/{repo}", settings);
    Console.WriteLine("Applied merge and branch-cleanup settings.");
}
var updated = await Api("GET", $"repos/{repo}");
var remaining = settings.Where(kv => updated?[kv.Key]?.ToJsonString() != JsonSerializer.Serialize(kv.Value)).Select(kv => kv.Key).ToArray();
var activeRules = await Api("GET", $"repos/{repo}/rulesets?includes_parents=false") as JsonArray ?? new JsonArray();
var matches = activeRules.Where(x => x?["name"]?.GetValue<string>() == "SUN Main Protection").ToArray();
var violations = new List<string>();
if (matches.Length != 1) violations.Add($"Expected exactly one SUN Main Protection ruleset; found {matches.Length}");
var active = matches.SingleOrDefault();
if (active?["enforcement"]?.GetValue<string>() != "active") violations.Add("Ruleset enforcement must be active");
if (active?["target"]?.GetValue<string>() != "branch") violations.Add("Ruleset target must be branch");
if (active is not null)
{
    var detail = await Api("GET", $"repos/{repo}/rulesets/{active["id"]}");
    var include = (detail?["conditions"]?["ref_name"]?["include"] as JsonArray)?.Select(x => x?.GetValue<string>()).ToArray();
    var exclude = detail?["conditions"]?["ref_name"]?["exclude"] as JsonArray;
    if (include is null || include.Length != 1 || include[0] != "refs/heads/main" || exclude is null || exclude.Count != 0)
        violations.Add("Ruleset must target only refs/heads/main without exclusions");
    if ((detail?["bypass_actors"] as JsonArray)?.Count != 0) violations.Add("Ruleset must have no bypass actors");
    var rs = detail?["rules"] as JsonArray ?? new JsonArray();
    foreach (var type in new[] { "deletion", "non_fast_forward", "pull_request", "required_status_checks" })
        if (rs.Count(x => x?["type"]?.GetValue<string>() == type) != 1) violations.Add($"Expected exactly one {type} rule");
    var required = rs.FirstOrDefault(x => x?["type"]?.GetValue<string>() == "required_status_checks");
    var pr = rs.FirstOrDefault(x => x?["type"]?.GetValue<string>() == "pull_request");
    if (required?["parameters"]?["strict_required_status_checks_policy"]?.GetValue<bool>() != true)
        violations.Add("Strict required status checks must be enabled");
    if (required?["parameters"]?["do_not_enforce_on_create"]?.GetValue<bool>() != false)
        violations.Add("Required checks must be enforced on creation");
    if (pr?["parameters"]?["required_review_thread_resolution"]?.GetValue<bool>() != true)
        violations.Add("PR review threads must be resolved");
    if (pr?["parameters"]?["required_approving_review_count"]?.GetValue<int>() != 0)
        violations.Add("Expected zero required approving reviews (baseline policy)");
    var actualChecks = (required?["parameters"]?["required_status_checks"] as JsonArray ?? new JsonArray())
        .Select(x => x?["context"]?.GetValue<string>()).Where(x => x is not null).Select(x => x!)
        .OrderBy(x => x, StringComparer.Ordinal).ToArray();
    var expectedChecks = checks.OrderBy(x => x, StringComparer.Ordinal).ToArray();
    if (!actualChecks.SequenceEqual(expectedChecks, StringComparer.Ordinal))
        violations.Add($"Required check mismatch. Expected [{string.Join(", ", expectedChecks)}]; actual [{string.Join(", ", actualChecks)}]");
}
foreach (var key in remaining) violations.Add($"Repository setting drift: {key}");
if (violations.Count > 0) throw new InvalidOperationException("Policy verification failed:\\n" + string.Join("\\n", violations));
Console.WriteLine("Verified: exact required checks, active main-only ruleset, no bypass actors, PR protection, merge settings and automatic branch deletion enabled.");
Console.WriteLine("NOTE: delete_branch_on_merge setting verified; actual post-merge branch removal still requires a disposable PR integration test.");
Console.WriteLine("MANUAL GATE: reviewer/CODEOWNERS enforcement and failing-CI merge protection remain separate integration tests.");
string? Arg(string name) { var i = Array.IndexOf(args, name); return i >= 0 && i + 1 < args.Length ? args[i + 1] : null; }
