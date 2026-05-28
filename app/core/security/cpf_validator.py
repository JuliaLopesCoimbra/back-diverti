"""
Validador de CPF brasileiro
Valida formato e dígitos verificadores
"""

def validate_cpf(cpf: str) -> str:
    """
    Valida e limpa CPF brasileiro.
    
    Args:
        cpf: CPF com ou sem formatação
        
    Returns:
        CPF limpo (apenas números, 11 dígitos)
        
    Raises:
        ValueError: Se o CPF for inválido
    """
    # Remove formatação (pontos, traços, espaços)
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf_clean) != 11:
        raise ValueError("CPF deve ter 11 dígitos.")
    
    # Verifica se todos os dígitos são iguais (CPF inválido)
    if cpf_clean == cpf_clean[0] * 11:
        raise ValueError("CPF inválido.")
    
    # Validação dos dígitos verificadores
    def calculate_digit(cpf_partial: str, weights: list) -> int:
        """Calcula um dígito verificador"""
        sum_result = sum(int(cpf_partial[i]) * weights[i] for i in range(len(cpf_partial)))
        remainder = sum_result % 11
        return 0 if remainder < 2 else 11 - remainder
    
    # Calcula primeiro dígito verificador
    weights_1 = list(range(10, 1, -1))
    digit_1 = calculate_digit(cpf_clean[:9], weights_1)
    
    if int(cpf_clean[9]) != digit_1:
        raise ValueError("CPF inválido.")
    
    # Calcula segundo dígito verificador
    weights_2 = list(range(11, 1, -1))
    digit_2 = calculate_digit(cpf_clean[:10], weights_2)
    
    if int(cpf_clean[10]) != digit_2:
        raise ValueError("CPF inválido.")
    
    return cpf_clean

