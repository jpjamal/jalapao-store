# Sistema Jalapão Store — site estático servido por nginx.
# O Traefik entrega em /jalapao-store sem remover o prefixo, por isso o site
# mora numa pasta com esse nome dentro da raiz do nginx: assim os links
# relativos (assets/jalapao.css) continuam resolvendo.

FROM nginx:1.27-alpine

COPY nginx-site.conf /etc/nginx/conf.d/default.conf
COPY site/ /usr/share/nginx/html/jalapao-store/

# /usr/share/nginx/html/manuais vem de volume do host — o PDF é enviado por SSH,
# fora do repositório, e por isso não entra na imagem.
RUN mkdir -p /usr/share/nginx/html/manuais

EXPOSE 80
