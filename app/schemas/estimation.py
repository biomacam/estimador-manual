from pydantic import BaseModel, Field


class EstimationRequest(BaseModel):
    transcription: str = Field(
        ..., description="Meeting transcription text to generate an estimation from"
    )


class UsageInfo(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class EstimationResponse(BaseModel):
    estimation: str = Field(..., description="Generated project estimation in markdown format")
    model: str = Field(..., description="LLM model used to generate the estimation")
    provider: str = Field(..., description="LLM provider used (openai or anthropic)")
    usage: UsageInfo = Field(..., description="Token usage for the LLM call")
