import logging
import re


class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        record.msg = scrub_sensitive_data(record.getMessage())
        return True


def scrub_sensitive_data(message):
    # Patterns for various API keys
    aws_access_key_pattern = r'AKIA[0-9A-Z]{16}'
    azure_client_id_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    generic_private_key_pattern = r'-----BEGIN [A-Z]+ PRIVATE KEY-----.+?-----END [A-Z]+ PRIVATE KEY-----'
    terraform_cloud_token_pattern_1 = r'atlasv1-[0-9a-z]{64}'
    terraform_cloud_token_pattern_2 = r'\b[a-zA-Z0-9]+\.atlasv1\.[a-zA-Z0-9]+'
    digitalocean_pat_pattern = r'[0-9a-f]{64}'
    cloudflare_global_api_key_pattern = r'[a-f0-9]{32}'

    # Replace patterns in the log message
    message = re.sub(aws_access_key_pattern, 'AKIAXXXXXXXXXXXXXXXX', message)
    message = re.sub(azure_client_id_pattern, 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX', message)
    message = re.sub(generic_private_key_pattern, '-----BEGIN PRIVATE KEY-----XXXX-----END PRIVATE KEY-----', message, flags=re.DOTALL)
    message = re.sub(terraform_cloud_token_pattern_1, 'atlasv1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', message)
    message = re.sub(terraform_cloud_token_pattern_2, 'xxxxxxxxxxxx.atlasv1.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', message)
    message = re.sub(digitalocean_pat_pattern, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', message)
    message = re.sub(cloudflare_global_api_key_pattern, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', message)
    return message


def setup_logger(log_level):
    # Set up logging with scrubbing filter
    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)
    logger.addFilter(SensitiveDataFilter())
    return logger


# # Example usage:
# logger = logging.getLogger(__name__)
# logger.addFilter(SensitiveDataFilter())
# logger.info("Starting app with AWS key AKIA1234567890ABCD")
