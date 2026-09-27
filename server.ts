import express from 'express';
import path from 'path';
import fs from 'fs';
import { spawn } from 'child_process';
import { createServer as createViteServer } from 'vite';

const app = express();
const PORT = 3000;

app.use(express.json({ limit: '10mb' }));

// Preset Software Engineering Requirements
const PRESETS = [
  {
    id: 'cli-calculator',
    title: 'Scientific & Financial CLI Calculator',
    badge: 'CLI Tool',
    prompt: 'Build a production-grade Scientific and Financial CLI Calculator with memory registers, trigonometry, compound interest formulas, error handling for division-by-zero, and full unit test coverage.',
    description: 'Modular architecture featuring clean domain models, operator strategy dispatchers, history tracking, and an extensive pytest verification suite.'
  },
  {
    id: 'kv-store',
    title: 'In-Memory Key-Value Store with TTL',
    badge: 'Core Engine',
    prompt: 'Build a high-performance in-memory Key-Value store with TTL key expiration, periodic background cleanup, atomic transactions (MULTI/EXEC), disk snapshotting/persistence, and comprehensive unit tests.',
    description: 'Thread-safe store implementing item timestamps, LRU eviction heuristics, serialized snapshots, and boundary assertions.'
  },
  {
    id: 'rest-todo',
    title: 'RESTful Task API with Priority Matrix',
    badge: 'Web Service',
    prompt: 'Build a clean RESTful Task & Project Management API with priority levels (URGENT, HIGH, MEDIUM, LOW), due date validators, tag filtering, pagination, and thorough pytest assertions.',
    description: 'Enterprise domain model with repository contracts, strict schema validation, CRUD endpoints, and robust mock transport layers.'
  },
  {
    id: 'event-bus',
    title: 'Publish-Subscribe Event Bus with Wildcards',
    badge: 'System Pattern',
    prompt: 'Build an asynchronous publish-subscribe Event Bus engine supporting hierarchical wildcard subscriptions (e.g. "order.*", "user.created"), synchronous/async handler dispatch, and dead-letter queues.',
    description: 'Decoupled architectural messaging bus with priority handlers, event replay capabilities, and comprehensive test suite.'
  }
];

// Health Check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Presets API
app.get('/api/pipeline/presets', (req, res) => {
  res.json({ presets: PRESETS });
});

// Helper to spawn cli_runner.py with args and parse PIPELINE_JSON
function runPipelineProcess(args: string[], res: express.Response) {
  const pyProcess = spawn('python3', args, {
    cwd: process.cwd(),
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  let stdoutData = '';
  let stderrData = '';

  pyProcess.stdout.on('data', (data) => {
    stdoutData += data.toString();
  });

  pyProcess.stderr.on('data', (data) => {
    stderrData += data.toString();
  });

  pyProcess.on('close', (code) => {
    if (code !== 0 && !stdoutData.includes('=== PIPELINE_JSON_START ===')) {
      console.error('Pipeline process failed with code', code, stderrData);
      return res.status(500).json({
        error: 'Multi-Agent Pipeline process failed',
        details: stderrData || stdoutData
      });
    }

    try {
      const startIndex = stdoutData.indexOf('=== PIPELINE_JSON_START ===');
      const endIndex = stdoutData.indexOf('=== PIPELINE_JSON_END ===');

      if (startIndex === -1 || endIndex === -1) {
        throw new Error('Could not parse pipeline JSON delimiter');
      }

      const rawJson = stdoutData.substring(
        startIndex + '=== PIPELINE_JSON_START ==='.length,
        endIndex
      ).trim();

      const pipelineState = JSON.parse(rawJson);
      return res.json({ success: true, pipeline: pipelineState });
    } catch (parseErr: any) {
      console.error('Failed to parse pipeline JSON:', parseErr, stdoutData);
      return res.status(500).json({
        error: 'Failed to parse pipeline output JSON',
        details: parseErr.message,
        raw: stdoutData.slice(0, 1000)
      });
    }
  });
}

// Run Multi-Agent Pipeline
app.post('/api/pipeline/run', (req, res) => {
  const { requirement, provider = 'deterministic', maxIterations = 3, apiKey, requireApproval = false } = req.body;

  if (!requirement || typeof requirement !== 'string' || !requirement.trim()) {
    return res.status(400).json({ error: 'Requirement prompt is required' });
  }

  const args = [
    'cli_runner.py',
    '--action', 'run',
    '--requirement', requirement.trim(),
    '--provider', provider,
    '--max-iterations', String(maxIterations)
  ];

  if (requireApproval) {
    args.push('--require-approval');
  }

  if (apiKey) {
    args.push('--api-key', apiKey);
  }

  runPipelineProcess(args, res);
});

// HITL Approval Gate: Approve & Continue
app.post('/api/pipeline/approve', (req, res) => {
  const { projectDir, reviewer = 'Human Operator' } = req.body;
  if (!projectDir) {
    return res.status(400).json({ error: 'projectDir is required' });
  }

  const args = [
    'cli_runner.py',
    '--action', 'approve',
    '--project-dir', projectDir,
    '--reviewer', reviewer
  ];

  runPipelineProcess(args, res);
});

// HITL Approval Gate: Request Changes with Feedback
app.post('/api/pipeline/request-changes', (req, res) => {
  const { projectDir, feedback, reviewer = 'Human Operator' } = req.body;
  if (!projectDir || !feedback || !feedback.trim()) {
    return res.status(400).json({ error: 'projectDir and non-empty feedback are required' });
  }

  const args = [
    'cli_runner.py',
    '--action', 'request-changes',
    '--project-dir', projectDir,
    '--feedback', feedback.trim(),
    '--reviewer', reviewer
  ];

  runPipelineProcess(args, res);
});

// HITL Approval Gate: Reject & Stop
app.post('/api/pipeline/reject', (req, res) => {
  const { projectDir, reason, reviewer = 'Human Operator' } = req.body;
  if (!projectDir) {
    return res.status(400).json({ error: 'projectDir is required' });
  }

  const args = [
    'cli_runner.py',
    '--action', 'reject',
    '--project-dir', projectDir,
    '--reviewer', reviewer
  ];

  if (reason && reason.trim()) {
    args.push('--reason', reason.trim());
  }

  runPipelineProcess(args, res);
});

// Push Git Repository to GitHub
app.post('/api/git/push-github', (req, res) => {
  const { projectDir, token, repoName, createNew = true, isPrivate = false } = req.body;

  if (!projectDir || !token || !repoName) {
    return res.status(400).json({ error: 'projectDir, token, and repoName are required' });
  }

  const script = `
import sys, json
from git_manager import GitManager

try:
    data = json.loads(sys.stdin.read())
    gm = GitManager(data.get("project_dir"))
    res = gm.push_to_github(
        token=data.get("token", ""),
        repo_name=data.get("repo_name", ""),
        create_new=data.get("create_new", True),
        is_private=data.get("is_private", False)
    )
    print("=== GITHUB_JSON_START ===")
    print(json.dumps(res))
    print("=== GITHUB_JSON_END ===")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
`;

  const py = spawn('python3', ['-c', script], {
    cwd: process.cwd()
  });

  let stdoutData = '';
  let stderrData = '';

  py.stdout.on('data', (d) => { stdoutData += d.toString(); });
  py.stderr.on('data', (d) => { stderrData += d.toString(); });

  py.stdin.write(JSON.stringify({
    project_dir: projectDir,
    token,
    repo_name: repoName,
    create_new: createNew,
    is_private: isPrivate
  }));
  py.stdin.end();

  py.on('close', (code) => {
    if (code !== 0 && !stdoutData.includes('=== GITHUB_JSON_START ===')) {
      return res.status(500).json({ error: 'GitHub push script failed', details: stderrData || stdoutData });
    }
    try {
      const s = stdoutData.indexOf('=== GITHUB_JSON_START ===') + '=== GITHUB_JSON_START ==='.length;
      const e = stdoutData.indexOf('=== GITHUB_JSON_END ===');
      const result = JSON.parse(stdoutData.substring(s, e).trim());
      if (result.success) {
        res.json({ success: true, ...result });
      } else {
        res.status(400).json({ success: false, error: result.error });
      }
    } catch (err: any) {
      res.status(500).json({ error: 'Failed to parse GitHub push response', details: err.message });
    }
  });
});

// Re-run Pytest in sandbox on current code files
app.post('/api/sandbox/run-tests', (req, res) => {
  const { codeFiles, testFiles } = req.body;

  if (!codeFiles || !testFiles) {
    return res.status(400).json({ error: 'codeFiles and testFiles required' });
  }

  const runnerScript = `
import json, sys
from dataclasses import asdict
from sandbox import SandboxExecutor

try:
    data = json.loads(sys.stdin.read())
    runner = SandboxExecutor()
    result = runner.execute_test_suite(data.get("code_files", {}), data.get("test_files", {}))
    print("=== SANDBOX_JSON_START ===")
    print(json.dumps(asdict(result)))
    print("=== SANDBOX_JSON_END ===")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
`;

  const pyProcess = spawn('python3', ['-c', runnerScript], {
    cwd: process.cwd()
  });

  let stdoutData = '';
  let stderrData = '';

  pyProcess.stdout.on('data', (d) => { stdoutData += d.toString(); });
  pyProcess.stderr.on('data', (d) => { stderrData += d.toString(); });

  pyProcess.stdin.write(JSON.stringify({ code_files: codeFiles, test_files: testFiles }));
  pyProcess.stdin.end();

  pyProcess.on('close', (code) => {
    if (code !== 0) {
      return res.status(500).json({ error: 'Sandbox run failed', details: stderrData });
    }
    try {
      const s = stdoutData.indexOf('=== SANDBOX_JSON_START ===') + '=== SANDBOX_JSON_START ==='.length;
      const e = stdoutData.indexOf('=== SANDBOX_JSON_END ===');
      const result = JSON.parse(stdoutData.substring(s, e).trim());
      res.json({ success: true, test_result: result });
    } catch (err: any) {
      res.status(500).json({ error: 'Failed to parse sandbox output', details: err.message });
    }
  });
});

// Git Diff for commit
app.get('/api/git/diff', (req, res) => {
  const { projectDir, commitHash } = req.query;
  if (!projectDir || !commitHash) {
    return res.status(400).json({ error: 'projectDir and commitHash query params are required' });
  }

  const script = `
import sys, json
from git_manager import GitManager
gm = GitManager(sys.argv[1])
diff_text = gm.get_diff(sys.argv[2])
print(diff_text)
`;

  const py = spawn('python3', ['-c', script, String(projectDir), String(commitHash)], {
    cwd: process.cwd()
  });

  let diffOutput = '';
  py.stdout.on('data', (d) => { diffOutput += d.toString(); });
  py.on('close', () => {
    res.json({ commit_hash: commitHash, diff: diffOutput });
  });
});

// Download Project ZIP archive
app.get('/api/git/download', (req, res) => {
  const { projectDir } = req.query;
  if (!projectDir || typeof projectDir !== 'string') {
    return res.status(400).json({ error: 'projectDir is required' });
  }

  if (!fs.existsSync(projectDir)) {
    return res.status(404).json({ error: 'Project directory not found' });
  }

  const script = `
import sys
from git_manager import GitManager
gm = GitManager(sys.argv[1])
zip_path = gm.export_zip()
print(zip_path)
`;

  const py = spawn('python3', ['-c', script, projectDir], {
    cwd: process.cwd()
  });

  let zipPath = '';
  py.stdout.on('data', (d) => { zipPath += d.toString(); });
  py.on('close', (code) => {
    const file = zipPath.trim();
    if (code === 0 && fs.existsSync(file)) {
      res.download(file, 'multiagent_software_project.zip', (err) => {
        // Clean up temp zip
        try { fs.unlinkSync(file); } catch (e) {}
      });
    } else {
      res.status(500).json({ error: 'Failed to create zip archive' });
    }
  });
});

// Vite Middleware for Dev / Static serving for Prod
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Multi-Agent Studio backend server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
