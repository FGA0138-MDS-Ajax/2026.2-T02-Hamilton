from django.http import JsonResponse
from django.shortcuts import render


class ErrorPageMiddleware:
    """
    Garante que URLs inválidas (404) e acessos a URLs sem permissão (403)
    exibam a página de erro no padrão visual do CoLecture
    (com o mascote, botão de voltar para pesquisa e visual do projeto),
    mantendo compatibilidade com testes e respostas de API (JSON).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Não interfere em respostas JSON ou requisições de API
        content_type = response.get('Content-Type', '')
        if isinstance(response, JsonResponse) or 'application/json' in content_type:
            return response

        # Se for 404 (URL inválida ou página não encontrada)
        if response.status_code == 404:
            content = getattr(response, 'content', b'').decode('utf-8', errors='ignore')
            # Se já for uma página customizada de livro ou comunidade que tem seu próprio bloco de erro
            if 'erro-img' in content or 'not-found' in content or 'erro-container' in content:
                return response

            return render(request, '404.html', {
                'title': 'Página não encontrada',
                'message': 'Essa página não existe, foi removida ou você não tem permissão para acessá-la.',
            }, status=404)

        # Se for 403 (Permissão negada / HttpResponseForbidden)
        elif response.status_code == 403:
            content = getattr(response, 'content', b'').decode('utf-8', errors='ignore')
            # Se já for uma página estilizada específica (ex: comunidade bloqueada ou já tem o container de erro)
            if 'blocked-page' in content or 'erro-container' in content:
                return response

            return render(request, '403.html', {
                'title': 'Página não encontrada',
                'message': 'Essa página não existe, foi removida ou você não tem permissão para acessá-la.',
            }, status=403)

        return response
