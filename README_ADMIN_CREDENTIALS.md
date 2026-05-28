# 🔐 Atualização de Credenciais do Admin Master

## ⚠️ IMPORTANTE DE SEGURANÇA

O admin master tem acesso total ao sistema. É **EXTREMAMENTE IMPORTANTE** que suas credenciais sejam:
- **Únicas** e não compartilhadas
- **Fortes** (mínimo 16 caracteres recomendado)
- **Armazenadas com segurança** (use um gerenciador de senhas)

## 📋 Como Atualizar as Credenciais

### Pré-requisitos

1. Acesso ao servidor onde o backend está rodando
2. Acesso ao banco de dados
3. Variáveis de ambiente configuradas (`.env`)

### Passos

1. **Navegue até o diretório do backend:**
   ```bash
   cd back-n1
   ```

2. **Execute o script:**
   ```bash
   python update_admin_credentials.py
   ```

3. **Siga as instruções:**
   - Digite `SIM` para confirmar que deseja continuar
   - Informe o novo email do admin master
   - Digite a nova senha (ela não será exibida na tela por segurança)
   - Confirme a senha
   - Digite `CONFIRMAR` para finalizar a alteração

### Requisitos da Senha

A senha deve atender aos seguintes requisitos:
- ✅ Mínimo 8 caracteres (recomendado 16+ para admin master)
- ✅ Pelo menos 1 letra maiúscula
- ✅ Pelo menos 1 letra minúscula
- ✅ Pelo menos 1 número
- ✅ Pelo menos 1 caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>/?)
- ✅ Pelo menos 3 tipos diferentes de caracteres

### Exemplo de Uso

```bash
$ python update_admin_credentials.py

======================================================================
🔐 ATUALIZAÇÃO DE CREDENCIAIS DO ADMIN MASTER
======================================================================

⚠️  ATENÇÃO: Este script irá alterar as credenciais do admin master.
    Certifique-se de que você tem autorização para fazer isso.

Deseja continuar? (digite 'SIM' para confirmar): SIM

📋 Buscando admin master no banco de dados...
✅ Admin master encontrado: admin@admin.com (ID: 1)

======================================================================
📧 NOVO EMAIL
======================================================================
Digite o novo email do admin master: admin.seguro@seudominio.com.br

======================================================================
🔑 NOVA SENHA
======================================================================
Requisitos de senha:
  • Mínimo 8 caracteres (recomendado 16+ para admin master)
  • Pelo menos 1 letra maiúscula
  • Pelo menos 1 letra minúscula
  • Pelo menos 1 número
  • Pelo menos 1 caractere especial
  • Pelo menos 3 tipos diferentes de caracteres

Digite a nova senha: [senha não será exibida]
Confirme a nova senha: [senha não será exibida]

======================================================================
⚠️  CONFIRMAÇÃO FINAL
======================================================================
Email atual: admin@admin.com
Email novo:  admin.seguro@seudominio.com.br
Senha: [OCULTA]

Confirma a alteração? (digite 'CONFIRMAR' para prosseguir): CONFIRMAR

🔄 Atualizando credenciais...

======================================================================
✅ CREDENCIAIS ATUALIZADAS COM SUCESSO!
======================================================================
Email: admin.seguro@seudominio.com.br
Senha: [ATUALIZADA]

⚠️  IMPORTANTE:
   1. Guarde essas credenciais em local seguro
   2. Não compartilhe essas credenciais
   3. Considere usar um gerenciador de senhas
   4. Faça logout de todas as sessões antigas se necessário
```

## 🔒 Boas Práticas de Segurança

1. **Use um gerenciador de senhas** (ex: 1Password, LastPass, Bitwarden)
2. **Gere senhas aleatórias** com pelo menos 16 caracteres
3. **Não compartilhe as credenciais** por email, chat ou outros meios inseguros
4. **Ative autenticação de dois fatores** se disponível no sistema
5. **Monitore logs de acesso** regularmente
6. **Altere a senha periodicamente** (recomendado a cada 90 dias)
7. **Use emails profissionais únicos** (não use emails genéricos como admin@admin.com)

## 🚨 Em Caso de Comprometimento

Se você suspeitar que as credenciais foram comprometidas:

1. **Execute o script imediatamente** para alterar as credenciais
2. **Revise os logs de acesso** do sistema
3. **Verifique atividades suspeitas** no banco de dados
4. **Notifique a equipe de segurança** se houver

## 📝 Notas Técnicas

- O script valida o formato do email antes de atualizar
- O script verifica se o email já está em uso por outro usuário
- A senha é hasheada usando Argon2 antes de ser armazenada
- Todas as operações são transacionais (rollback em caso de erro)
- O script não exibe a senha em nenhum momento

## ❓ Problemas Comuns

### Erro: "Admin master não encontrado"
- Verifique se o admin master existe no banco de dados
- Verifique se o role está como "admin_master" (não "admin")

### Erro: "Email já está em uso"
- O email informado já está sendo usado por outro usuário
- Escolha um email diferente

### Erro de conexão com banco de dados
- Verifique as variáveis de ambiente no arquivo `.env`
- Verifique se o banco de dados está acessível
- Verifique as credenciais de conexão

