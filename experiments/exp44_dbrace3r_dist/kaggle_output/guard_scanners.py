"""Minimal llm-guard replacement: Secrets + PromptInjection scanners only.

The real `llm_guard.input_scanners` package __init__ imports every scanner
(Anonymize -> presidio -> spacy/thinc, Toxicity, ...), which native-crashes the
Kaggle kernel (DeadKernelError on import). This module re-implements ONLY the
two scanners private_guard uses, with identical behavior:

  - SecretsScanner == llm_guard.input_scanners.Secrets:
    bc-detect-secrets with llm-guard's exact plugin list (16 built-ins,
    94 custom plugins extracted from the llm-guard 0.3.16 wheel,
    Base64HighEntropyString limit 4.5, HexHighEntropyString limit 3.0).
    Returns is_valid=False when any secret with a recovered value is found.
  - PromptInjectionScanner(threshold) == PromptInjection(V2_MODEL, SENTENCE):
    protectai/deberta-v3-base-prompt-injection-v2 (pinned revision), text split
    by nltk.sent_tokenize, per-sentence INJECTION score vs threshold.

Both expose llm-guard's scan(prompt) -> (prompt, is_valid, score) contract.
"""

from __future__ import annotations

import os
import tempfile

_PLUGINS_DIR = "/kaggle/working/secrets_plugins"

_CUSTOM_PLUGINS = [
    ("AdafruitKeyDetector", "adafruit.py"),
    ("AdobeSecretDetector", "adobe.py"),
    ("AgeSecretKeyDetector", "age_secret_key.py"),
    ("AirtableApiKeyDetector", "airtable_api_key.py"),
    ("AlgoliaApiKeyDetector", "algolia_api_key.py"),
    ("AlibabaSecretDetector", "alibaba.py"),
    ("AsanaSecretDetector", "asana.py"),
    ("AtlassianApiTokenDetector", "atlassian_api_token.py"),
    ("AuthressAccessKeyDetector", "authress_access_key.py"),
    ("BittrexDetector", "beamer_api_token.py"),
    ("BitbucketDetector", "bitbucket.py"),
    ("BeamerApiTokenDetector", "bittrex.py"),
    ("ClojarsApiTokenDetector", "clojars_api_token.py"),
    ("CodecovAccessTokenDetector", "codecov_access_token.py"),
    ("CoinbaseAccessTokenDetector", "coinbase_access_token.py"),
    ("ConfluentDetector", "confluent.py"),
    ("ContentfulApiTokenDetector", "contentful_api_token.py"),
    ("DatabricksApiTokenDetector", "databricks_api_token.py"),
    ("DatadogAccessTokenDetector", "datadog_access_token.py"),
    ("DefinedNetworkingApiTokenDetector", "defined_networking_api_token.py"),
    ("DigitaloceanDetector", "digitalocean.py"),
    ("DopplerApiTokenDetector", "doppler_api_token.py"),
    ("DroneciAccessTokenDetector", "droneci_access_token.py"),
    ("DuffelApiTokenDetector", "duffel_api_token.py"),
    ("DynatraceApiTokenDetector", "dynatrace_api_token.py"),
    ("DiscordDetector", "discord.py"),
    ("DropboxDetector", "dropbox.py"),
    ("EasyPostDetector", "easypost.py"),
    ("EtsyAccessTokenDetector", "etsy_access_token.py"),
    ("FacebookAccessTokenDetector", "facebook_access_token.py"),
    ("FastlyApiKeyDetector", "fastly_api_token.py"),
    ("FinicityDetector", "finicity.py"),
    ("FinnhubAccessTokenDetector", "finnhub_access_token.py"),
    ("FlickrAccessTokenDetector", "flickr_access_token.py"),
    ("FlutterwaveDetector", "flutterwave.py"),
    ("FrameIoApiTokenDetector", "frameio_api_token.py"),
    ("FreshbooksAccessTokenDetector", "freshbooks_access_token.py"),
    ("GCPApiKeyDetector", "gcp_api_key.py"),
    ("GitHubTokenCustomDetector", "github_token.py"),
    ("GitLabDetector", "gitlab.py"),
    ("GitterAccessTokenDetector", "gitter_access_token.py"),
    ("GoCardlessApiTokenDetector", "gocardless_api_token.py"),
    ("GrafanaDetector", "grafana.py"),
    ("HashiCorpTFApiTokenDetector", "hashicorp_tf_api_token.py"),
    ("HerokuApiKeyDetector", "heroku_api_key.py"),
    ("HubSpotApiTokenDetector", "hubspot_api_key.py"),
    ("HuggingFaceDetector", "huggingface.py"),
    ("IntercomApiTokenDetector", "intercom_api_key.py"),
    ("JFrogDetector", "jfrog.py"),
    ("JWTBase64Detector", "jwt.py"),
    ("KrakenAccessTokenDetector", "kraken_access_token.py"),
    ("KucoinDetector", "kucoin.py"),
    ("LaunchdarklyAccessTokenDetector", "launchdarkly_access_token.py"),
    ("LinearDetector", "linear.py"),
    ("LinkedInDetector", "linkedin.py"),
    ("LobDetector", "lob.py"),
    ("MailgunDetector", "mailgun.py"),
    ("MapBoxApiTokenDetector", "mapbox_api_token.py"),
    ("MattermostAccessTokenDetector", "mattermost_access_token.py"),
    ("MessageBirdDetector", "messagebird.py"),
    ("MicrosoftTeamsWebhookDetector", "microsoft_teams_webhook.py"),
    ("NetlifyAccessTokenDetector", "netlify_access_token.py"),
    ("NewRelicDetector", "new_relic.py"),
    ("NYTimesAccessTokenDetector", "nytimes_access_token.py"),
    ("OktaAccessTokenDetector", "okta_access_token.py"),
    ("OpenAIApiKeyDetector", "openai_api_key.py"),
    ("PlanetScaleDetector", "planetscale.py"),
    ("PostmanApiTokenDetector", "postman_api_token.py"),
    ("PrefectApiTokenDetector", "prefect_api_token.py"),
    ("PulumiApiTokenDetector", "pulumi_api_token.py"),
    ("PyPiUploadTokenDetector", "pypi_upload_token.py"),
    ("RapidApiAccessTokenDetector", "rapidapi_access_token.py"),
    ("ReadmeApiTokenDetector", "readme_api_token.py"),
    ("RubygemsApiTokenDetector", "rubygems_api_token.py"),
    ("ScalingoApiTokenDetector", "scalingo_api_token.py"),
    ("SendbirdDetector", "sendbird.py"),
    ("SendGridApiTokenDetector", "sendgrid_api_token.py"),
    ("SendinBlueApiTokenDetector", "sendinblue_api_token.py"),
    ("SentryAccessTokenDetector", "sentry_access_token.py"),
    ("ShippoApiTokenDetector", "shippo_api_token.py"),
    ("ShopifyDetector", "shopify.py"),
    ("SidekiqDetector", "sidekiq.py"),
    ("SlackDetector", "slack.py"),
    ("SnykApiTokenDetector", "snyk_api_token.py"),
    ("SquarespaceAccessTokenDetector", "squarespace_access_token.py"),
    ("SumoLogicDetector", "sumologic.py"),
    ("TelegramBotApiTokenDetector", "telegram_bot_api_token.py"),
    ("TravisCiAccessTokenDetector", "travisci_access_token.py"),
    ("TwitchApiTokenDetector", "twitch_api_token.py"),
    ("TwitterDetector", "twitter.py"),
    ("TypeformApiTokenDetector", "typeform_api_token.py"),
    ("VaultDetector", "vault.py"),
    ("YandexDetector", "yandex.py"),
    ("ZendeskSecretKeyDetector", "zendesk_secret_key.py"),
]

_BUILTIN_DETECTORS = [
    "SoftlayerDetector",
    "StripeDetector",
    "NpmDetector",
    "IbmCosHmacDetector",
    "DiscordBotTokenDetector",
    "BasicAuthDetector",
    "AzureStorageKeyDetector",
    "ArtifactoryDetector",
    "AWSKeyDetector",
    "CloudantDetector",
    "IbmCloudIamDetector",
    "JwtTokenDetector",
    "MailchimpDetector",
    "SquareOAuthDetector",
    "PrivateKeyDetector",
    "TwilioKeyDetector",
]

_DETECT_SECRETS_CONFIG = {
    "plugins_used": (
        [{"name": n} for n in _BUILTIN_DETECTORS]
        + [
            {"name": n, "path": "file://" + os.path.join(_PLUGINS_DIR, f)}
            for n, f in _CUSTOM_PLUGINS
        ]
        + [
        {"name": "Base64HighEntropyString", "limit": 4.5},
        {"name": "HexHighEntropyString", "limit": 3.0},
        ]
    )
}


class SecretsScanner:
    """detect-secrets backed credential/secret scanner (llm-guard Secrets)."""

    def scan(self, prompt: str) -> tuple[str, bool, float]:
        from detect_secrets.core.secrets_collection import SecretsCollection
        from detect_secrets.settings import transient_settings

        if prompt.strip() == "":
            return prompt, True, -1.0

        secrets = SecretsCollection()
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
            tmp.write(prompt.encode("utf-8"))
            tmp.close()
            with transient_settings(_DETECT_SECRETS_CONFIG):
                secrets.scan_file(str(tmp.name))
        finally:
            os.remove(tmp.name)

        found = any(
            s.secret_value is not None
            for f in secrets.files
            for s in secrets[f]
        )
        return prompt, not found, (1.0 if found else -1.0)


class PromptInjectionScanner:
    """ProtectAI deberta-v3 prompt-injection scanner, per-sentence match
    (llm-guard PromptInjection with V2_MODEL + MatchType.SENTENCE)."""

    def __init__(self, *, threshold: float = 0.85) -> None:
        self._threshold = threshold
        import nltk
        try:
            nltk.data.find("tokenizers/punkt_tab")
        except LookupError:
            nltk.download("punkt_tab", quiet=True)
        from transformers import pipeline
        self._pipeline = pipeline(
            task="text-classification",
            model="protectai/deberta-v3-base-prompt-injection-v2",
            revision="89b085cd330414d3e7d9dd787870f315957e1e9f",
            return_token_type_ids=False,
            max_length=512,
            truncation=True,
        )

    def scan(self, prompt: str) -> tuple[str, bool, float]:
        import nltk
        if prompt.strip() == "":
            return prompt, True, -1.0
        sentences = nltk.sent_tokenize(prompt.strip()) or [prompt]
        highest = 0.0
        for result in self._pipeline(sentences):
            score = round(
                result["score"] if result["label"] == "INJECTION" else 1 - result["score"],
                2,
            )
            if score > highest:
                highest = score
            if score > self._threshold:
                return prompt, False, 1.0
        return prompt, True, highest
