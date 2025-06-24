#!/usr/bin/env python3

"""
Test suite for client.py
"""

import unittest
from unittest.mock import patch, PropertyMock, MagicMock
from parameterized import parameterized, parameterized_class
import fixtures
from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """
    Test class for client.GithubOrgClient
    """

    @parameterized.expand([
        ('google', {
            'login': 'google', 'id': 1342004,
            'node_id': 'MDEyOk9yZ2FuaXphdGlvbjEzNDIwMDQ=',
            'url': 'https://api.github.com/orgs/google',
            'repos_url': 'https://api.github.com/orgs/google/repos',
            'events_url': 'https://api.github.com/orgs/google/events',
            'hooks_url': 'https://api.github.com/orgs/google/hooks',
            'issues_url': 'https://api.github.com/orgs/google/issues',
            'members_url': 'https://api.github.com/' +
            'orgs/google/members{/member}',
            'public_members_url': 'https://api.github.com/' +
            'orgs/google/public_members{/member}',
            'avatar_url': 'https://avatars.githubusercontent.com/' +
            'u/1342004?v=4',
            'description': 'Google ❤️ Open Source', 'name': 'Google',
            'company': None, 'blog': 'https://opensource.google/',
            'location': 'United States of America',
            'email': 'opensource@google.com', 'twitter_username': 'GoogleOSS',
            'is_verified': True, 'has_organization_projects': True,
            'has_repository_projects': True, 'public_repos': 2770,
            'public_gists': 0, 'followers': 54958, 'following': 0,
            'html_url': 'https://github.com/google',
            'created_at': '2012-01-18T01:30:18Z',
            'updated_at': '2024-08-09T17:36:18Z',
            'archived_at': None, 'type': 'Organization'}),
        ('abc', {
            'message': 'Not Found',
            'documentation_url': 'https://docs.github.com/' +
            'rest/orgs/orgs#get-an-organization',
            'status': '404'
            }),
    ])
    @patch('client.get_json')
    def test_org(self, org_name, response_msg, mock_get_json):
        """
        Test that GithubOrgClient.org returns the correct value.
        """
        mock_get_json.return_value = response_msg
        new_client = GithubOrgClient(org_name)
        output = new_client.org
        mock_get_json.assert_called_once_with(
            f"https://api.github.com/orgs/{org_name}"
            )
        self.assertDictEqual(output, response_msg)

    def test_public_repos_url(self):
        """
        Test method for GithubOrgClient._public_repos_url
        """
        with patch(
            'client.GithubOrgClient.org', new_callable=PropertyMock
        ) as mock_org:
            mock_org.return_value = {
                'login': 'google', 'id': 1342004,
                'node_id': 'MDEyOk9yZ2FuaXphdGlvbjEzNDIwMDQ=',
                'url': 'https://api.github.com/orgs/google',
                'repos_url': 'https://api.github.com/orgs/google/repos',
                'events_url': 'https://api.github.com/orgs/google/events',
                'hooks_url': 'https://api.github.com/orgs/google/hooks',
                'issues_url': 'https://api.github.com/orgs/google/issues',
                'members_url': 'https://api.github.com/' +
                'orgs/google/members{/member}',
                'public_members_url': 'https://api.github.com/' +
                'orgs/google/public_members{/member}',
                'avatar_url': 'https://avatars.githubusercontent.com/' +
                'u/1342004?v=4',
                'description': 'Google ❤️ Open Source', 'name': 'Google',
                'company': None, 'blog': 'https://opensource.google/',
                'location': 'United States of America',
                'email': 'opensource@google.com',
                'twitter_username': 'GoogleOSS',
                'is_verified': True, 'has_organization_projects': True,
                'has_repository_projects': True, 'public_repos': 2770,
                'public_gists': 0, 'followers': 54958, 'following': 0,
                'html_url': 'https://github.com/google',
                'created_at': '2012-01-18T01:30:18Z',
                'updated_at': '2024-08-09T17:36:18Z',
                'archived_at': None, 'type': 'Organization'
                }

            new_client = GithubOrgClient('google')
            url = new_client._public_repos_url
            self.assertEqual(url, 'https://api.github.com/orgs/google/repos')

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """
        Test function for GithubOrgClient.public_repos
        """
        mock_get_json.return_value = [
            {"id": 1936771, "name": "truth"},
            {"id": 3248507, "name": "ruby-openid-apps-discovery"},
            {"id": 3248531, "name": "autoparse"},
            {"id": 3975462, "name": "anvil-build"},
            {"id": 5072378, "name": "googletv-android-samples"},
            {"id": 5511393, "name": "ChannelPlate"},
            {"id": 5753459, "name": "GL-Shader-Validator"},
            {"id": 5753483, "name": "qpp"},
            {"id": 5815969, "name": "CSP-Validator"},
            {"id": 5844236, "name": "embed-dart-vm"},
            {"id": 6093488, "name": "module-server"},
            {"id": 6461354, "name": "cxx-std-draft"},
            {"id": 6461358, "name": "filesystem-proposal"},
            {"id": 6461369, "name": "libcxx"},
            {"id": 6601918, "name": "tracing-framework"},
            {"id": 6694773, "name": "namebench"},
            {"id": 7411412, "name": "devtoolsExtended"},
            {"id": 7411424, "name": "sirius"},
            {"id": 7411426, "name": "testRunner"},
            {"id": 7411430, "name": "crx2app"},
            {"id": 7697149, "name": "episodes.dart"},
            {"id": 7776515, "name": "cpp-netlib"},
            {"id": 7968417, "name": "dagger"},
            {"id": 8165161, "name": "ios-webkit-debug-proxy"},
            {"id": 8459994, "name": "google.github.io"},
            {"id": 8566972, "name": "kratu"},
            {"id": 8858648, "name": "build-debian-cloud"},
            {"id": 9060347, "name": "traceur-compiler"},
            {"id": 9065917, "name": "firmata.py"},
            {"id": 9402340, "name": "vector_math.dart"}
            ]

        with patch(
            'client.GithubOrgClient._public_repos_url',
            new_callable=PropertyMock
        ) as mock_public_repos_url:
            mock_public_repos_url.return_value = '' \
                'https://api.github.com/orgs/google/repos'

            new_client = GithubOrgClient('google')
            repos = new_client.public_repos()

            self.assertListEqual(
                repos, [
                    'truth', 'ruby-openid-apps-discovery', 'autoparse',
                    'anvil-build', 'googletv-android-samples', 'ChannelPlate',
                    'GL-Shader-Validator', 'qpp', 'CSP-Validator',
                    'embed-dart-vm', 'module-server', 'cxx-std-draft',
                    'filesystem-proposal', 'libcxx', 'tracing-framework',
                    'namebench', 'devtoolsExtended', 'sirius', 'testRunner',
                    'crx2app', 'episodes.dart', 'cpp-netlib', 'dagger',
                    'ios-webkit-debug-proxy', 'google.github.io', 'kratu',
                    'build-debian-cloud', 'traceur-compiler', 'firmata.py',
                    'vector_math.dart'
                    ]
                )

            mock_public_repos_url.assert_called_once()
            mock_get_json.assert_called_once_with(
                "https://api.github.com/orgs/google/repos"
                )

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo, license_key, status):
        """
        Test function for GithubOrgClient.has_license
        """
        self.assertIs(GithubOrgClient.has_license(repo, license_key), status)


@parameterized_class([
    {
        "org_payload": fixtures.TEST_PAYLOAD[0][0],
        "repos_payload": fixtures.TEST_PAYLOAD[0][1],
        "expected_repos": fixtures.TEST_PAYLOAD[0][2],
        "apache2_repos": fixtures.TEST_PAYLOAD[0][3]
        }
])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """
    Integration Test Suite
    """

    @classmethod
    def setUpClass(cls):
        """
        Sets ups mocks for requests.get to return
        example payloads found in the fixtures.
        """
        cls.get_patcher = patch("requests.get")
        cls.mock_get = cls.get_patcher.start()

        mock_org_response = MagicMock()
        mock_org_response.json.return_value = cls.org_payload

        mock_repos_response = MagicMock()
        mock_repos_response.json.return_value = cls.repos_payload

        cls.mock_get.side_effect = [
            mock_org_response,
            mock_repos_response,
            ]

    @classmethod
    def tearDownClass(cls):
        """
        class method to stop the patcher
        """
        cls.get_patcher.stop()

    def test_public_repos(self):
        """
        Test function for GithubOrgClient.public_repos
        """
        client = GithubOrgClient('google')
        self.assertEqual(
            client._public_repos_url, self.org_payload["repos_url"]
            )
        repos = client.public_repos()
        self.assertListEqual(repos, self.expected_repos)
