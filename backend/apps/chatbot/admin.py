"""
Configuração do painel administrativo Django para o módulo do Chatbot Lumia.

Registra os modelos de sessão e mensagem para visualização, auditoria e gestão
pela equipe pedagógica e técnica no painel nativo do Django (/admin).
"""
from django.contrib import admin
from .models import SessaoChat, MensagemChat


@admin.register(SessaoChat)
class AdministradorSessaoChat(admin.ModelAdmin):
    """Configura a exibição e os filtros das sessões de chat no Django Admin."""
    list_display = ('id', 'usuario', 'criado_em', 'atualizado_em')
    list_filter = ('criado_em', 'atualizado_em')
    search_fields = ('usuario__username', 'usuario__email', 'id')
    ordering = ('-atualizado_em',)


@admin.register(MensagemChat)
class AdministradorMensagemChat(admin.ModelAdmin):
    """Configura a exibição e os filtros das mensagens individuais de chat no Django Admin."""
    list_display = ('id', 'sessao', 'papel', 'criado_em')
    list_filter = ('papel', 'criado_em')
    search_fields = ('conteudo', 'sessao__id')
    ordering = ('criado_em',)


# Aliases para compatibilidade
ChatSessionAdmin = AdministradorSessaoChat
ChatMessageAdmin = AdministradorMensagemChat
