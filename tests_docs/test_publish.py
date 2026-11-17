# this_file: tests_docs/test_publish.py
"""Exercise publishing against owned local Git remotes; no live API writes."""
import os
import shlex
import shutil
import subprocess
import tempfile
import unittest

import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT = shutil.which('git')


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.repo = self.folder / 'repo'
        self.remote = self.folder / 'remote.git'
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1')
        self.env.pop('GIT_INDEX_FILE', None)
        subprocess.run([GIT, 'init', '--bare', str(self.remote)], check=True, capture_output=True)
        subprocess.run([GIT, 'init', '-b', 'main', str(self.repo)], check=True, capture_output=True)
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'docs').mkdir()
        (self.repo / 'docs/index.html').write_text('old')
        (self.repo / 'source.txt').write_text('source')
        self.git('add', '.')
        self.git('commit', '-m', 'fixture')
        self.git('remote', 'add', 'origin', str(self.remote))
        self.git('push', 'origin', 'HEAD:main')
        self.sha = self.git('rev-parse', 'HEAD').strip()
        self.env['GITHUB_OUTPUT'] = str(self.folder / 'output')
        self.env['GITHUB_REPOSITORY'] = 'fixture/fontlab-python-pens'

    def git(self, *args):
        return subprocess.check_output([GIT, '-C', str(self.repo), *args], env=self.env, text=True, stderr=subprocess.STDOUT)

    def run_script(self, name, sha=None):
        return subprocess.run(['sh', str(ROOT / 'src_docs' / name), sha or self.sha], cwd=self.repo, env=self.env, text=True, capture_output=True, check=False)

    def test_changed_docs_commit_only_output_and_preserve_source(self):
        (self.repo / 'docs/index.html').write_text('new')
        (self.repo / 'source.txt').write_text('uncommitted owner data')
        result = self.run_script('publish.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        current = self.git('rev-parse', 'HEAD').strip()
        self.assertNotEqual(current, self.sha)
        self.assertEqual(self.git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').strip(), 'docs/index.html')
        self.assertEqual(self.git('show', 'HEAD:source.txt'), 'source')
        self.assertEqual((self.repo / 'source.txt').read_text(), 'uncommitted owner data')
        self.assertEqual((self.folder / 'output').read_text(), f'sha={current}\n')
        self.assertIn(current, self.git('ls-remote', 'origin', 'refs/heads/main'))

    def test_unchanged_docs_keep_existing_commit(self):
        result = self.run_script('publish.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.sha)
        self.assertEqual((self.folder / 'output').read_text(), f'sha={self.sha}\n')

    def test_superseded_source_does_not_commit_or_emit_output(self):
        self.git('commit', '--allow-empty', '-m', 'new source')
        self.git('push', 'origin', 'HEAD:main')
        self.git('checkout', self.sha)
        (self.repo / 'docs/index.html').write_text('old run')
        result = self.run_script('publish.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('superseded', result.stdout)
        self.assertFalse((self.folder / 'output').exists())
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.sha)

    def test_wrong_checkout_and_preexisting_staged_data_fail(self):
        result = self.run_script('publish.sh', '0' * 40)
        self.assertNotEqual(result.returncode, 0)
        (self.repo / 'source.txt').write_text('staged owner data')
        self.git('add', 'source.txt')
        result = self.run_script('publish.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git('diff', '--cached', '--name-only').strip(), 'source.txt')

    def test_push_rejection_is_failure_and_does_not_emit_output(self):
        hook = self.remote / 'hooks/pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        (self.repo / 'docs/index.html').write_text('new')
        result = self.run_script('publish.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.folder / 'output').exists())
        self.assertIn(self.sha, self.git('ls-remote', 'origin', 'refs/heads/main'))





    def test_competing_commit_between_guard_and_push_is_preserved(self):
        tree = self.git('rev-parse', 'HEAD^{tree}').strip()
        concurrent = self.git('commit-tree', tree, '-p', self.sha, '-m', 'concurrent owner').strip()
        hook = self.repo / '.git/hooks/pre-push'
        command = [GIT, '--git-dir=' + str(self.remote), 'fetch', str(self.repo), concurrent + ':refs/heads/main']
        hook.write_text('#!/bin/sh\n' + shlex.join(command) + '\n')
        hook.chmod(0o755)
        (self.repo / 'docs/index.html').write_text('racing output')
        result = self.run_script('publish.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.folder / 'output').exists())
        self.assertIn(concurrent, self.git('ls-remote', 'origin', 'refs/heads/main'))


    def test_unreachable_origin_fails_without_commit_output_or_staging(self):
        self.git('remote', 'set-url', 'origin', str(self.folder / 'absent.git'))
        (self.repo / 'docs/index.html').write_text('new output')
        result = self.run_script('publish.sh')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.folder / 'output').exists())
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.sha)
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')

    def test_remote_missing_main_fails_without_commit_output_or_staging(self):
        subprocess.run([GIT, '--git-dir=' + str(self.remote), 'update-ref', '-d', 'refs/heads/main'], check=True)
        (self.repo / 'docs/index.html').write_text('new output')
        result = self.run_script('publish.sh')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.folder / 'output').exists())
        self.assertEqual(self.git('rev-parse', 'HEAD').strip(), self.sha)
        self.assertEqual(self.git('diff', '--cached', '--name-only'), '')

    def run_workflow_check(self, name, **updates):
        workflow = yaml.safe_load((ROOT / '.github/workflows/docs.yml').read_text())
        step = next(s for s in workflow['jobs']['qualify-generated-output']['steps'] if s.get('name') == name)
        env = dict(self.env, SOURCE_SHA=self.sha, OUTPUT_SHA=self.git('rev-parse', 'HEAD').strip(), SOURCE_DATE_EPOCH=self.git('show', '-s', '--format=%ct', self.sha).strip())
        env.update(updates)
        return subprocess.run(['sh', '-eu', '-c', step['run']], cwd=self.repo, env=env, text=True, capture_output=True)

    def test_immutable_lineage_accepts_source_and_direct_docs_only_child(self):
        self.assertEqual(self.run_workflow_check('Verify immutable output lineage').returncode, 0)
        (self.repo / 'docs/index.html').write_text('generated')
        self.git('add', 'docs')
        self.git('commit', '-m', 'generated')
        result = self.run_workflow_check('Verify immutable output lineage')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_immutable_lineage_rejects_source_change_wrong_epoch_wrong_head_and_grandchild(self):
        for updates in ({'SOURCE_DATE_EPOCH': '0'}, {'OUTPUT_SHA': '0' * 40}):
            self.assertNotEqual(self.run_workflow_check('Verify immutable output lineage', **updates).returncode, 0)
        (self.repo / 'source.txt').write_text('foreign source')
        self.git('add', 'source.txt')
        self.git('commit', '-m', 'foreign source')
        self.assertNotEqual(self.run_workflow_check('Verify immutable output lineage').returncode, 0)
        (self.repo / 'docs/index.html').write_text('generated grandchild')
        self.git('add', 'docs')
        self.git('commit', '-m', 'grandchild')
        self.assertNotEqual(self.run_workflow_check('Verify immutable output lineage').returncode, 0)

    def test_full_parity_rejects_tracked_and_untracked_even_ignored_output(self):
        self.assertEqual(self.run_workflow_check('Require committed output parity').returncode, 0)
        (self.repo / 'docs/index.html').write_text('changed')
        self.assertNotEqual(self.run_workflow_check('Require committed output parity').returncode, 0)
        (self.repo / 'docs/index.html').write_text('old')
        (self.repo / '.git/info/exclude').write_text('docs/ignored.html\n')
        (self.repo / 'docs/ignored.html').write_text('unexpected')
        self.assertNotEqual(self.run_workflow_check('Require committed output parity').returncode, 0)

    def test_ordinary_local_pre_push_refusal_is_not_bypassed(self):
        hook = self.repo / '.git/hooks/pre-push'
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        (self.repo / 'docs/index.html').write_text('new')
        result = self.run_script('publish.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.folder / 'output').exists())
        self.assertIn(self.sha, self.git('ls-remote', 'origin', 'refs/heads/main'))
