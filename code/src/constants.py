import enum

VCR_HEADERS_EXCLUDE = ["Authorization", "Api-Key"]

DAY_IN_SECONDS = 24 * 3600


class SupportedVectorStores(str, enum.Enum):
    opengauss = "opengauss"


class SupportedEmbeddings(str, enum.Enum):
    openai = "OpenAI"
    cohere = "Cohere"
    fake = "Fake"
