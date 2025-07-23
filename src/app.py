import os
from logging_config import logger
import uvicorn
import requests
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
from openai import OpenAI
from dependencies import has_access
from typing import Dict
from utils import is_safe_to_edit

def build_prompt(option: str, language: str, page: str) -> str:

    if option == "make_shorter":
        if language in ("pt_BR", "pt_PT"):
            return ("Você é um analista de redes sociais e deve reduzir o texto da resposta para envio a um consumidor"
                    if page == "crm"
                    else "Você é um social media e deve reduzir o texto para realizar uma publicação")
        if language == "es":
            return ("Eres analista de redes sociales y debes reducir el texto de respuesta para enviarlo a un consumidor"
                    if page == "crm"
                    else "Eres un social media y debes reducir el texto para hacer una publicación")
        if language == "en":
            return ("You are a social media analyst and must reduce response text to send to a consumer"
                    if page == "crm"
                    else "You are a social media and must reduce the text to make a publication")

    elif option == "make_longer":
        if language in ("pt_BR", "pt_PT"):
            return ("Você é um analista de redes sociais e deve aumentar o texto da resposta para envio a um consumidor"
                    if page == "crm"
                    else "Você é um social media e deve aumentar o texto para realizar uma publicação")
        if language == "es":
            return ("Eres analista de redes sociales y debes aumentar el texto de respuesta para enviar a un consumidor"
                    if page == "crm"
                    else "Eres un social media y debes aumentar el texto para hacer una publicación")
        if language == "en":
            return ("You are a social media analyst and you must increase the response text to send to a consumer"
                    if page == "crm"
                    else "You are a social media and must increase the text to make a publication")

    elif option == "improve_writing":
        if language in ("pt_BR", "pt_PT"):
            return ("Você é um analista de redes sociais e deve melhorar a escrita da resposta para envio a um consumidor"
                    if page == "crm"
                    else "Você é um social media e deve melhorar a escrita para realizar uma publicação")
        if language == "es":
            return ("Eres analista de redes sociales y necesitas mejorar tu redacción de respuestas para enviarlo a un consumidor"
                    if page == "crm"
                    else "Eres un social media y debes mejorar tu redacción para hacer una publicación")
        if language == "en":
            return ("You are a social media analyst and you need to improve your response writing to send to a consumer"
                    if page == "crm"
                    else "You are a social media and you must improve your writing to make a publication")

    elif option == "fix_spelling_grammar":
        return {
            "pt_BR": "Corrija a ortografia e gramática do texto a seguir",
            "pt_PT": "Corrija a ortografia e gramática do texto a seguir",
            "es":    "Corrija la ortografía y la gramática del siguiente texto",
            "en":    "Fix the spelling and grammar of the following text",
        }.get(language, "Corrija a ortografia e gramática do texto a seguir")

    # Se nada combinar, devolve string vazia (ou poderia lançar exceção)
    return ""

def gpt_answer(
    text: str,
    page: str,
    option: str,
    language: str,
    account_open_ai_token: str,
    user_commercial_email: str,
    user_master_commercial_email: str
    ) -> dict:
    
    input_tokens = 0
    output_tokens = 0
    prompt = build_prompt(option, language, page)
    if not prompt:
        return {"answer": text, "status_code": 400, "input_tokens": 0, "output_tokens": 0}
    prompt_aux = {"pt_BR": ". Retorne somente o texto",
                  "pt_PT": ". Retorne somente o texto",
                  "es":    ". Retorne solo el texto",
                  "en":    ". Return only the text"}.get(language, ". Retorne somente o texto")
    try:
        openai_client = OpenAI(
            api_key=account_open_ai_token,
        )  
        completion = openai_client.chat.completions.create(
            model='gpt-4.1-nano',
            messages=[
                    {
                    "content": f"{prompt}. {prompt_aux}: {text}",
                    "role": "user"
                    }
            ],
            temperature= 0.7
        )

        input_tokens = completion.usage.prompt_tokens
        output_tokens = completion.usage.completion_tokens
        answer = completion.choices[0].message.content

    except requests.RequestException as exc:
        logger.error(f"[ai-text-edit] Erro de requisição para OpenAI API: {exc}")
        return {"answer": text, "status_code": 500, "input_tokens": 0, "output_tokens": 0}

    logger.info(
        f"[ai-text-edit] User {user_master_commercial_email} ({user_commercial_email}) consumed {input_tokens} input tokens and {output_tokens} output tokens.",
     )
    return {"answer": answer, "status_code": 200, "input_tokens": input_tokens, "output_tokens": output_tokens}


# ------------------------------------------------------------------
# -----------------------  FASTAPI BOILERPLATE  --------------------
# ------------------------------------------------------------------
app = FastAPI(
    docs_url=None,  # Desativa docs padrão
    redoc_url=None,  # Desativa redoc padrão
    title="Buzzmonitor Text Edit API",
    version="1.0.0",
    description="Serviço que faz chamadas à OpenAI para encurtar, "
                "estender ou aprimorar textos dependendo do idioma."
)
@app.head("/alive")
@app.get("/alive")
def alive():
    return "alive"

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

@app.get("/docs", include_in_schema=False)
def get_documentation(auth=Depends(has_access)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Buzzmonitor Text Edit API Docs")

@app.get("/openapi.json", include_in_schema=False)
def openapi(auth=Depends(has_access)):
    return get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)



# -----------  Esquemas Pydantic para request / response -----------
class GPTRequest(BaseModel):
    user_account_open_ai_token:str
    user_commercial_email:str
    user_master_commercial_email:str
    language:Literal["pt_BR", "pt_PT", "en", "es"] = Field(..., description="Idioma do texto")
    text: str = Field(..., description="Texto a ser processado")
    
    page: Literal["crm", "publish"] = Field(..., description="Contexto da página")
    option: Literal[
        "make_shorter", "make_longer", "improve_writing", "fix_spelling_grammar"
    ] = Field(..., description="Ação desejada sobre o texto")


class GPTResponse(BaseModel):
    answer: str
    input_tokens: int
    output_tokens: int
    


@app.post(
    "/gpt-answer",
    response_model=GPTResponse,
    status_code=status.HTTP_200_OK,
    summary="Processar texto com GPT",
    dependencies=[Depends(has_access)]  
)
def gpt_answer_route(payload: GPTRequest) -> GPTResponse:
    if not is_safe_to_edit(payload.text):
        raise HTTPException(status_code=400, detail=f"Texto inválido '{payload.text}'!")
    
    result = gpt_answer(
        text=payload.text,
        page=payload.page,
        option=payload.option,
        language=payload.language,
        account_open_ai_token=payload.user_account_open_ai_token,
        user_commercial_email=payload.user_commercial_email,
        user_master_commercial_email=payload.user_master_commercial_email
    )

    if result["status_code"] != 200:
        raise HTTPException(status_code=result["status_code"], detail="Erro ao consultar GPT")
    return GPTResponse(answer=result["answer"], input_tokens=result["input_tokens"], output_tokens=result["output_tokens"])
