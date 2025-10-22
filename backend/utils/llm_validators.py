# backend/utils/llm_validators.py
"""
Validadores robustos para saídas de LLMs.
Previne erros de parsing e garante dados consistentes.
"""

import re
from typing import Optional, Tuple, Dict, Any
from pydantic import BaseModel, ValidationError
from .logger import logger


# ============================================
# VALIDADOR DE CÓDIGO MERMAID
# ============================================

def validate_mermaid_syntax(code: str) -> Tuple[bool, str]:
    """
    Valida sintaxe básica de código Mermaid.
    
    Args:
        code: Código Mermaid a validar
        
    Returns:
        tuple: (is_valid, error_message)
    """
    
    if not code or not code.strip():
        return False, "Código vazio"
    
    code = code.strip()
    
    # Remove markdown wrappers se houver
    code = re.sub(r'^```mermaid\s*', '', code, flags=re.MULTILINE)
    code = re.sub(r'\s*```$', '', code, flags=re.MULTILINE)
    code = code.strip()
    
    # 1. Deve começar com 'mindmap'
    if not code.startswith('mindmap'):
        return False, "Código não começa com 'mindmap'"
    
    # 2. Deve ter um título central com {{...}}
    if not re.search(r'\{\{.*?\}\}', code):
        return False, "Título central {{...}} não encontrado"
    
    # 3. Verifica caracteres problemáticos que podem quebrar o Mermaid
    problematic_chars = [
        (r'[^\s]\(', "Parênteses '(' detectados (use '-' ou ':' no lugar)"),
        (r'\)[^\s]', "Parênteses ')' detectados (use '-' ou ':' no lugar)"),
        (r'\[(?![^\]]*\])', "Colchetes '[' mal formatados"),
    ]
    
    for pattern, msg in problematic_chars:
        if re.search(pattern, code):
            return False, msg
    
    # 4. Verifica níveis de indentação (múltiplos de 2)
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        if line.strip() and not line.strip().startswith('mindmap'):
            # Conta espaços iniciais
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces % 2 != 0:
                return False, f"Linha {i}: indentação inválida (não é múltiplo de 2)"
    
    # 5. Verifica se tem pelo menos um ícone
    if not re.search(r'::icon\(fa fa-[\w-]+\)', code):
        logger.warning("Nenhum ícone encontrado no mapa (não é erro crítico)")
    
    return True, ""


def clean_mermaid_code(code: str) -> str:
    """
    Limpa código Mermaid removendo wrappers e caracteres problemáticos.
    
    Args:
        code: Código Mermaid bruto
        
    Returns:
        str: Código limpo
    """
    
    # Remove markdown wrappers
    code = re.sub(r'^```mermaid\s*', '', code, flags=re.MULTILINE)
    code = re.sub(r'\s*```$', '', code, flags=re.MULTILINE)
    
    # Remove linhas vazias extras
    lines = [line for line in code.split('\n') if line.strip()]
    code = '\n'.join(lines)
    
    # Substitui parênteses problemáticos por alternativas
    # Nota: Isso é agressivo - use com cuidado
    # code = code.replace('(', '-').replace(')', '-')
    
    return code.strip()


# ============================================
# VALIDADOR DE DIVISÃO DE CONTEÚDO
# ============================================

def validate_divisao_response(response: Any) -> Tuple[bool, str, Optional[Dict]]:
    """
    Valida resposta do LLM01 (divisor).
    
    Args:
        response: Resposta do LLM (Pydantic model ou dict)
        
    Returns:
        tuple: (is_valid, error_message, cleaned_data)
    """
    
    try:
        # Se é Pydantic model, converte para dict
        if hasattr(response, 'model_dump'):
            data = response.model_dump()
        elif isinstance(response, dict):
            data = response
        else:
            return False, f"Tipo de resposta inválido: {type(response)}", None
        
        # Validações básicas
        if 'num_partes' not in data:
            return False, "Campo 'num_partes' ausente", None
        
        if 'partes' not in data:
            return False, "Campo 'partes' ausente", None
        
        num_partes = data['num_partes']
        partes = data['partes']
        
        # Valida número de partes
        if not isinstance(num_partes, int) or num_partes < 2 or num_partes > 10:
            return False, f"num_partes inválido: {num_partes} (esperado: 2-10)", None
        
        # Valida lista de partes
        if not isinstance(partes, list):
            return False, "Campo 'partes' não é uma lista", None
        
        if len(partes) != num_partes:
            return False, f"Inconsistência: num_partes={num_partes} mas len(partes)={len(partes)}", None
        
        # Valida cada parte
        for i, parte in enumerate(partes, 1):
            if not isinstance(parte, dict):
                return False, f"Parte {i} não é um dict", None
            
            # Campos obrigatórios
            required_fields = ['numero', 'titulo', 'conteudo_completo']
            for field in required_fields:
                if field not in parte:
                    return False, f"Parte {i}: campo '{field}' ausente", None
            
            # Valida conteúdo
            conteudo = parte.get('conteudo_completo', '')
            if not conteudo or len(conteudo) < 100:
                return False, f"Parte {i}: conteúdo muito curto ({len(conteudo)} chars, mínimo 100)", None
            
            # Valida número da parte
            if parte['numero'] != i:
                logger.warning(f"Parte {i}: número inconsistente (esperado {i}, encontrado {parte['numero']})")
                parte['numero'] = i  # Corrige
        
        logger.success(f"✅ Divisão validada: {num_partes} partes, total {sum(len(p['conteudo_completo']) for p in partes)} chars")
        
        return True, "", data
        
    except Exception as e:
        logger.error(f"Erro na validação de divisão: {e}")
        return False, f"Erro na validação: {str(e)}", None


# ============================================
# VALIDADOR DE AVALIAÇÃO (REVISOR)
# ============================================

def validate_avaliacao_response(response: Any) -> Tuple[bool, str, Optional[Dict]]:
    """
    Valida resposta do LLM03 (revisor).
    
    Args:
        response: Resposta do LLM (Pydantic model ou dict)
        
    Returns:
        tuple: (is_valid, error_message, cleaned_data)
    """
    
    try:
        # Converte para dict
        if hasattr(response, 'model_dump'):
            data = response.model_dump()
        elif isinstance(response, dict):
            data = response
        else:
            return False, f"Tipo de resposta inválido: {type(response)}", None
        
        # Campos obrigatórios
        required_fields = ['aprovado', 'nota_geral', 'problemas', 'justificativa']
        for field in required_fields:
            if field not in data:
                return False, f"Campo '{field}' ausente", None
        
        # Valida tipos
        if not isinstance(data['aprovado'], bool):
            return False, f"Campo 'aprovado' deve ser bool, não {type(data['aprovado'])}", None
        
        # Valida nota
        nota = data['nota_geral']
        if not isinstance(nota, (int, float)):
            return False, f"Campo 'nota_geral' deve ser número, não {type(nota)}", None
        
        if nota < 0 or nota > 10:
            logger.warning(f"Nota fora do range: {nota}. Ajustando...")
            data['nota_geral'] = max(0, min(10, nota))
        
        # Valida problemas
        if not isinstance(data['problemas'], list):
            logger.warning("Campo 'problemas' não é lista. Convertendo...")
            data['problemas'] = []
        
        # Valida sugestões
        if 'sugestoes_melhoria' not in data:
            data['sugestoes_melhoria'] = []
        
        if not isinstance(data['sugestoes_melhoria'], list):
            data['sugestoes_melhoria'] = []
        
        logger.success(
            f"✅ Avaliação validada: {'APROVADO' if data['aprovado'] else 'REJEITADO'}, "
            f"nota {data['nota_geral']:.1f}, {len(data['problemas'])} problemas"
        )
        
        return True, "", data
        
    except Exception as e:
        logger.error(f"Erro na validação de avaliação: {e}")
        return False, f"Erro na validação: {str(e)}", None


# ============================================
# VALIDADOR GENÉRICO DE STRUCTURED OUTPUT
# ============================================

def validate_structured_output(
    response: Any,
    expected_model: type[BaseModel],
    fallback_on_error: bool = True
) -> Tuple[bool, str, Optional[Any]]:
    """
    Valida structured output de qualquer LLM.
    
    Args:
        response: Resposta do LLM
        expected_model: Modelo Pydantic esperado
        fallback_on_error: Se True, retorna fallback em vez de falhar
        
    Returns:
        tuple: (is_valid, error_message, validated_data)
    """
    
    try:
        # Se já é instância do modelo esperado
        if isinstance(response, expected_model):
            return True, "", response
        
        # Se é dict, tenta criar instância
        if isinstance(response, dict):
            validated = expected_model(**response)
            return True, "", validated
        
        # Tipo inesperado
        return False, f"Tipo inesperado: {type(response)}", None
        
    except ValidationError as e:
        error_msg = f"Erro de validação: {e}"
        logger.error(error_msg)
        
        if fallback_on_error:
            # Retorna dados brutos mesmo com erro
            logger.warning("⚠️ Usando dados não validados como fallback")
            return False, error_msg, response
        
        return False, error_msg, None
    
    except Exception as e:
        error_msg = f"Erro inesperado: {e}"
        logger.error(error_msg)
        return False, error_msg, None


# ============================================
# HELPER: EXTRAÇÃO SEGURA DE CONTEÚDO
# ============================================

def safe_extract_content(response: Any, field: str, default: Any = None) -> Any:
    """
    Extrai campo de resposta de LLM de forma segura.
    
    Args:
        response: Resposta do LLM (dict, Pydantic model, ou string)
        field: Nome do campo a extrair
        default: Valor padrão se extração falhar
        
    Returns:
        Valor extraído ou default
    """
    
    try:
        # Se é Pydantic model
        if hasattr(response, field):
            return getattr(response, field)
        
        # Se é dict
        if isinstance(response, dict):
            return response.get(field, default)
        
        # Se é string (resposta sem structured output)
        if isinstance(response, str):
            logger.warning(f"Resposta é string, não estruturada. Retornando default para '{field}'")
            return default
        
        logger.warning(f"Tipo inesperado: {type(response)}. Retornando default para '{field}'")
        return default
        
    except Exception as e:
        logger.error(f"Erro ao extrair '{field}': {e}")
        return default


# ============================================
# EXEMPLO DE USO
# ============================================

if __name__ == "__main__":
    # Teste de validação de Mermaid
    mermaid_valido = """
mindmap
  {{**Teste**}}
    **Item 1**
    ::icon(fa fa-check)
      Sub 1
      Sub 2
    """
    
    mermaid_invalido = """
mindmap
  Sem chaves duplas
    Item (com parênteses)
    """
    
    print("Testando Mermaid válido:")
    valid, msg = validate_mermaid_syntax(mermaid_valido)
    print(f"  {'✅' if valid else '❌'} {msg if msg else 'OK'}")
    
    print("\nTestando Mermaid inválido:")
    valid, msg = validate_mermaid_syntax(mermaid_invalido)
    print(f"  {'✅' if valid else '❌'} {msg if msg else 'OK'}")