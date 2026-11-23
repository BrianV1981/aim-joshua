"""TDD regression suite for Issue #140: Multi-repo issue number collision guards in aim_projects.py."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(REPO_ROOT, "joshua_os", ".aim_core")

if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)


def test_issue_140_find_item_by_issue_rejects_cross_repo_and_substring_collisions():
    """find_item_by_issue must never match another repository's issue #<N> on shared multi-repo boards."""
    import aim_projects

    board_items = [
        {
            "id": "PVTI_youtube_14",
            "status": "Done",
            "content": {
                "type": "Issue",
                "number": 14,
                "title": "Wave 2 Video Recon",
                "repository": "AcmeOrg/aim-youtube",
                "url": "https://github.com/AcmeOrg/aim-youtube/issues/14",
            },
        },
        {
            "id": "PVTI_content_14",
            "status": "In Progress",
            "content": {
                "type": "Issue",
                "number": 14,
                "title": "Content Spoke Article",
                "repository": "AcmeOrg/aim-site-content",
                "url": "https://github.com/AcmeOrg/aim-site-content/issues/14",
            },
        },
    ]

    # 1. Requesting AcmeOrg/aim-browser#14 must NOT collide with AcmeOrg/aim-youtube#14
    assert aim_projects.find_item_by_issue(board_items, 14, repo="AcmeOrg/aim-browser") is None

    # 2. Prefix substring repo ("AcmeOrg/aim-site") must NOT collide with "AcmeOrg/aim-site-content"
    assert aim_projects.find_item_by_issue(board_items, 14, repo="AcmeOrg/aim-site") is None
    assert aim_projects.find_item_by_issue(board_items, 14, repo="aim-site") is None

    # 3. Different owner with same slug ("OtherOrg/aim-youtube") must NOT match "AcmeOrg/aim-youtube"
    assert aim_projects.find_item_by_issue(board_items, 14, repo="OtherOrg/aim-youtube") is None

    # 4. Exact owner/repo (case-insensitive) and bare repo slug match cleanly
    hit_full = aim_projects.find_item_by_issue(board_items, 14, repo="acmeorg/aim-youtube")
    assert hit_full is not None and hit_full["id"] == "PVTI_youtube_14"

    hit_slug = aim_projects.find_item_by_issue(board_items, 14, repo="aim-site-content")
    assert hit_slug is not None and hit_slug["id"] == "PVTI_content_14"

    # 5. Passing already-normalized items preserves repository attribution without double-normalizing
    normalized_items = [aim_projects.normalize_item(i) for i in board_items]
    assert aim_projects.find_item_by_issue(normalized_items, 14, repo="AcmeOrg/aim-browser") is None
    hit_norm = aim_projects.find_item_by_issue(normalized_items, 14, repo="AcmeOrg/aim-youtube")
    assert hit_norm is not None and hit_norm["id"] == "PVTI_youtube_14"

    # 6. normalize_item extracts owner/repo fallback from content.url when content.repository is absent
    url_only_item = {
        "id": "PVTI_url_only_14",
        "content": {
            "type": "Issue",
            "number": 14,
            "title": "URL-only item",
            "url": "https://github.com/AcmeOrg/aim-browser/issues/14",
        },
    }
    norm_url = aim_projects.normalize_item(url_only_item)
    assert norm_url["repository"] == "AcmeOrg/aim-browser"
    hit_url = aim_projects.find_item_by_issue(board_items + [url_only_item], 14, repo="AcmeOrg/aim-browser")
    assert hit_url is not None and hit_url["id"] == "PVTI_url_only_14"


def test_issue_140_detect_repo_parses_git_remote_before_gh():
    """_detect_repo extracts owner/name directly from remote.origin.url (SSH & HTTPS) without requiring gh network calls."""
    import aim_projects

    with patch("aim_projects.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="git@github.com:AcmeOrg/aim-joshua.git\n", stderr=""
        )
        assert aim_projects._detect_repo() == "AcmeOrg/aim-joshua"
        assert mock_run.call_count == 1  # Resolved via local git config without invoking gh

        mock_run.reset_mock()
        mock_run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="https://github.com/AcmeOrg/aim-connect/\n", stderr=""
        )
        assert aim_projects._detect_repo() == "AcmeOrg/aim-connect"
        assert mock_run.call_count == 1


def test_issue_140_unmocked_cli_projects_set_adds_target_repo_without_mutating_sibling_issue(tmp_path):
    """Real './aim projects --repo AcmeOrg/aim-browser --number 7 --owner AcmeOrg set 14 Backlog' subprocess E2E."""
    bin_dir = tmp_path / "fake_bin"
    bin_dir.mkdir()
    calls_log = tmp_path / "gh_calls.jsonl"

    gh_py = bin_dir / "gh_shim.py"
    gh_py.write_text(
        "import json, os, sys\n"
        "args = sys.argv[1:]\n"
        "log_path = os.environ['FAKE_GH_LOG']\n"
        "with open(log_path, 'a', encoding='utf-8') as f:\n"
        "    f.write(json.dumps(args) + '\\n')\n"
        "if args[:2] == ['project', 'view']:\n"
        "    print(json.dumps({'id': 'PVT_board_7', 'title': 'Shared Fleet Board'}))\n"
        "elif args[:2] == ['project', 'field-list']:\n"
        "    print(json.dumps({'fields': [{'id': 'PVTF_status', 'name': 'Status', 'options': [\n"
        "        {'id': 'OPT_backlog', 'name': 'Backlog'},\n"
        "        {'id': 'OPT_done', 'name': 'Done'}\n"
        "    ]}]}))\n"
        "elif args[:2] == ['project', 'item-list']:\n"
        "    print(json.dumps({'items': [{\n"
        "        'id': 'PVTI_youtube_14',\n"
        "        'status': 'Done',\n"
        "        'content': {\n"
        "            'type': 'Issue',\n"
        "            'number': 14,\n"
        "            'title': 'Closed YouTube Issue 14',\n"
        "            'repository': 'AcmeOrg/aim-youtube',\n"
        "            'url': 'https://github.com/AcmeOrg/aim-youtube/issues/14'\n"
        "        }\n"
        "    }]}))\n"
        "elif args[:2] == ['project', 'item-add']:\n"
        "    print(json.dumps({\n"
        "        'id': 'PVTI_browser_14',\n"
        "        'content': {\n"
        "            'type': 'Issue',\n"
        "            'number': 14,\n"
        "            'title': 'Browser Headless Parity',\n"
        "            'repository': 'AcmeOrg/aim-browser',\n"
        "            'url': 'https://github.com/AcmeOrg/aim-browser/issues/14'\n"
        "        }\n"
        "    }))\n"
        "elif args[:2] == ['project', 'item-edit']:\n"
        "    print('ok')\n"
        "else:\n"
        "    sys.exit(2)\n",
        encoding="utf-8",
    )

    if os.name == "nt":
        shim = bin_dir / "gh.cmd"
        shim.write_text(f'@"{sys.executable}" "{gh_py}" %*\r\n', encoding="utf-8")
    else:
        shim = bin_dir / "gh"
        shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{gh_py}" "$@"\n', encoding="utf-8")
        shim.chmod(0o755)

    launcher = os.path.join(REPO_ROOT, "aim.cmd" if os.name == "nt" else "aim")
    env = os.environ.copy()
    env["FAKE_GH_LOG"] = str(calls_log)
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")

    res = subprocess.run(
        [
            launcher,
            "projects",
            "--owner",
            "AcmeOrg",
            "--number",
            "7",
            "--repo",
            "AcmeOrg/aim-browser",
            "set",
            "14",
            "Backlog",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert "AcmeOrg/aim-browser#14" in res.stdout
    assert "Status: Backlog" in res.stdout

    logged = [json.loads(line) for line in calls_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    add_calls = [c for c in logged if c[:2] == ["project", "item-add"]]
    edit_calls = [c for c in logged if c[:2] == ["project", "item-edit"]]

    assert len(add_calls) == 1
    assert "https://github.com/AcmeOrg/aim-browser/issues/14" in add_calls[0]
    assert len(edit_calls) == 1
    assert "PVTI_browser_14" in edit_calls[0]
    assert "PVTI_youtube_14" not in edit_calls[0]
