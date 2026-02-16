"""Web UI routes: request list and detail pages."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from smello_server.models import CapturedRequest

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def request_list(
    request: Request,
    host: str | None = Query(None),
    method: str | None = Query(None),
    status: int | None = Query(None),
    search: str | None = Query(None),
    _partial: str | None = Query(None),
):
    from smello_server.app import templates

    qs = CapturedRequest.all()
    if host:
        qs = qs.filter(host=host)
    if method:
        qs = qs.filter(method=method.upper())
    if status:
        qs = qs.filter(status_code=status)
    if search:
        qs = qs.filter(url__icontains=search)

    requests_list = await qs.limit(100)

    hosts = await CapturedRequest.all().distinct().values_list("host", flat=True)
    methods = await CapturedRequest.all().distinct().values_list("method", flat=True)

    context = {
        "request": request,
        "requests": requests_list,
        "hosts": sorted(set(hosts)),
        "methods": sorted(set(methods)),
        "filter_host": host or "",
        "filter_method": method or "",
        "filter_status": status or "",
        "filter_search": search or "",
        "selected_id": "",
    }

    if _partial == "list":
        return templates.TemplateResponse("partials/request_list_items.html", context)

    return templates.TemplateResponse("request_list.html", context)


@router.get("/requests/{request_id}", response_class=HTMLResponse)
async def request_detail(request: Request, request_id: str):
    from smello_server.app import templates

    captured = await CapturedRequest.get(id=request_id)

    return templates.TemplateResponse(
        "request_detail.html",
        {
            "request": request,
            "captured": captured,
        },
    )


@router.get("/requests/{request_id}/partial", response_class=HTMLResponse)
async def request_detail_partial(request: Request, request_id: str):
    from smello_server.app import templates

    captured = await CapturedRequest.get(id=request_id)

    return templates.TemplateResponse(
        "partials/request_detail_partial.html",
        {
            "request": request,
            "captured": captured,
        },
    )
