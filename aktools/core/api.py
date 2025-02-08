# -*- coding:utf-8 -*-
# /usr/bin/env python
"""
Date: 2024/1/12 22:05
Desc: HTTP 模式主文件
"""
import asyncio
import json
import logging
import urllib.parse
from logging.handlers import TimedRotatingFileHandler

import akshare as ak
from fastapi import APIRouter, WebSocket, FastAPI
from fastapi import Depends, status
from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from aktools.datasets import get_pyscript_html, get_template_path
from aktools.login.user_login import User, get_current_active_user

app_core = APIRouter()

# 创建一个日志记录器
logger = logging.getLogger(name='AKToolsLog')
logger.setLevel(logging.INFO)

# 创建一个TimedRotatingFileHandler来进行日志轮转
handler = TimedRotatingFileHandler(
    filename='aktools_log.log', when='midnight', interval=1, backupCount=7, encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 使用日志记录器记录信息
logger.info('这是一个信息级别的日志消息')


@app_core.get("/private/{item_id}", description="私人接口", summary="该接口主要提供私密访问来获取数据")
def root(
        request: Request,
        item_id: str,
        current_user: User = Depends(get_current_active_user),
):
    """
    接收请求参数及接口名称并返回 JSON 数据
    此处由于 AKShare 的请求中是同步模式，所以这边在定义 root 函数中没有使用 asyncio 来定义，这样可以开启多线程访问
    :param request: 请求信息
    :type request: Request
    :param item_id: 必选参数; 测试接口名 ak.stock_dxsyl_em() 来获取 打新收益率 数据
    :type item_id: str
    :param current_user: 依赖注入，为了进行用户的登录验证
    :type current_user: str
    :return: 指定 接口名称 和 参数 的数据
    :rtype: json
    """
    interface_list = dir(ak)
    decode_params = urllib.parse.unquote(str(request.query_params))
    # print(decode_params)
    if item_id not in interface_list:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz"
            },
        )
    eval_str = decode_params.replace("&", '", ').replace("=", '="') + '"'
    if not bool(request.query_params):
        try:
            received_df = eval("ak." + item_id + "()")
            if received_df is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": "该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz"},
                )
            temp_df = received_df.to_json(orient="records", date_format="iso")
        except KeyError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz"
                },
            )
        return JSONResponse(status_code=status.HTTP_200_OK, content=json.loads(temp_df))
    else:
        try:
            received_df = eval("ak." + item_id + f"({eval_str})")
            if received_df is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": "该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz"},
                )
            temp_df = received_df.to_json(orient="records", date_format="iso")
        except KeyError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz"
                },
            )
        return JSONResponse(status_code=status.HTTP_200_OK, content=json.loads(temp_df))


@app_core.get(path="/public/{item_id}", description="公开接口", summary="该接口主要提供公开访问来获取数据")
def root(request: Request, item_id: str):
    """
    接收请求参数及接口名称并返回 JSON 数据
    此处由于 AKShare 的请求中是同步模式，所以这边在定义 root 函数中没有使用 asyncio 来定义，这样可以开启多线程访问
    :param request: 请求信息
    :type request: Request
    :param item_id: 必选参数; 测试接口名 stock_dxsyl_em 来获取 打新收益率 数据
    :type item_id: str
    :return: 指定 接口名称 和 参数 的数据
    :rtype: json
    """
    interface_list = dir(ak)
    decode_params = urllib.parse.unquote(str(request.query_params))
    # print(decode_params)
    if item_id not in interface_list:
        logger.info("未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz"
            },
        )
    if "cookie" in decode_params:
        eval_str = (
                decode_params.split(sep="=", maxsplit=1)[0]
                + "='"
                + decode_params.split(sep="=", maxsplit=1)[1]
                + "'"
        )
        eval_str = eval_str.replace("+", " ")
    else:
        eval_str = decode_params.replace("&", '", ').replace("=", '="') + '"'
        eval_str = eval_str.replace("+", " ")  # 处理传递的参数中带空格的情况
    if not bool(request.query_params):
        try:
            received_df = eval("ak." + item_id + "()")
            if received_df is None:
                logger.info("该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": "该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz"},
                )
            temp_df = received_df.to_json(orient="records", date_format="iso")
        except KeyError as e:
            logger.info(
                f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz"
                },
            )
        logger.info(f"获取到 {item_id} 的数据")
        return JSONResponse(status_code=status.HTTP_200_OK, content=json.loads(temp_df))
    else:
        try:
            received_df = eval("ak." + item_id + f"({eval_str})")
            if received_df is None:
                logger.info("该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz")
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": "该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz"},
                )
            temp_df = received_df.to_json(orient="records", date_format="iso")
        except KeyError as e:
            logger.info(
                f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz"
                },
            )
        logger.info(f"获取到 {item_id} 的数据")
        return JSONResponse(status_code=status.HTTP_200_OK, content=json.loads(temp_df))


def generate_html_response():
    file_path = get_pyscript_html(file="akscript.html")
    with open(file_path, encoding="utf8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)


short_path = get_template_path()
templates = Jinja2Templates(directory=short_path)


@app_core.get(
    path="/show-temp/{interface}",
    response_class=HTMLResponse,
    description="展示 PyScript",
    summary="该接口主要展示 PyScript 游览器运行 Python 代码",
)
def akscript_temp(request: Request, interface: str):
    return templates.TemplateResponse(
        "akscript.html",
        context={
            "request": request,
            "ip": request.headers["host"],
            "interface": interface,
        },
    )


@app_core.get(
    path="/show",
    response_class=HTMLResponse,
    description="展示 PyScript",
    summary="该接口主要展示 PyScript 游览器运行 Python 代码",
)
def akscript():
    return generate_html_response()


@app_core.websocket("/ws/public")
async def websocket_public(websocket: WebSocket):
    semaphore = asyncio.Semaphore(2)
    await websocket.accept()
    try:
        async def handle_message_with_semaphore(message, websocket):
            async with semaphore:
                handle_message(message, websocket)

        while True:
            # 接收客户端发送的消息
            message = await websocket.receive_text()
            asyncio.create_task(handle_message_with_semaphore(message, websocket))
    except Exception as e:
        logger.error(f"WebSocket 通信出现错误: {e}")
    finally:
        await websocket.close()

async def handle_message(message, websocket):
    try:
        # 解析客户端消息，期望消息是包含 messageId、item_id 和 params 的 JSON
        data = json.loads(message)
        message_id = data.get("messageId")
        item_id = data.get("item_id")
        params_str = data.get("params", "")
        if not item_id:
            error_message = {
                "messageId": message_id,
                "error": "缺少 item_id 参数"
            }
            await websocket.send_text(json.dumps(error_message))
            return
        interface_list = dir(ak)
        decode_params = urllib.parse.unquote(params_str)
        if item_id not in interface_list:
            logger.info("未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz")
            error_message = {
                "messageId": message_id,
                "error": "未找到该接口，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz"
            }
            await websocket.send_text(json.dumps(error_message))
            return
        if "cookie" in decode_params:
            eval_str = (
                    decode_params.split(sep="=", maxsplit=1)[0]
                    + "='"
                    + decode_params.split(sep="=", maxsplit=1)[1]
                    + "'"
            )
            eval_str = eval_str.replace("+", " ")
        else:
            eval_str = decode_params.replace("&", '", ').replace("=", '="') + '"'
            eval_str = eval_str.replace("+", " ")  # 处理传递的参数中带空格的情况
        if not bool(params_str):
            try:
                received_df = eval("ak." + item_id + "()")
                if received_df is None:
                    logger.info("该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz")
                    error_message = {
                        "messageId": message_id,
                        "error": "该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz"
                    }
                    await websocket.send_text(json.dumps(error_message))
                    return
                temp_df = received_df.to_json(orient="records", date_format="iso")
            except KeyError as e:
                logger.info(
                    f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz")
                error_message = {
                    "messageId": message_id,
                    "error": f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz"
                }
                await websocket.send_text(json.dumps(error_message))
                return
            logger.info(f"获取到 {item_id} 的数据")
            response = {
                "messageId": message_id,
                "data": json.loads(temp_df)
            }
            await websocket.send_text(json.dumps(response))
        else:
            try:
                received_df = eval("ak." + item_id + f"({eval_str})")
                if received_df is None:
                    logger.info("该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz")
                    error_message = {
                        "messageId": message_id,
                        "error": "该接口返回数据为空，请确认参数是否正确：https://akshare.akfamily.xyz"
                    }
                    await websocket.send_text(json.dumps(error_message))
                    return
                temp_df = received_df.to_json(orient="records", date_format="iso")
            except KeyError as e:
                logger.info(
                    f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz")
                error_message = {
                    "messageId": message_id,
                    "error": f"请输入正确的参数错误 {e}，请升级 AKShare 到最新版本并在文档中确认该接口的使用方式：https://akshare.akfamily.xyz"
                }
                await websocket.send_text(json.dumps(error_message))
                return
            logger.info(f"获取到 {item_id} 的数据")
            response = {
                "messageId": message_id,
                "data": json.loads(temp_df)
            }
            await websocket.send_text(json.dumps(response))
    except json.JSONDecodeError:
        error_message = {
            "messageId": None,
            "error": "接收到的消息不是有效的 JSON 格式"
        }
        await websocket.send_text(json.dumps(error_message))

@app_core.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # 接受客户端的 WebSocket 连接
    print(f"Accepting WebSocket connection...")
    await websocket.accept()
    try:
        while True:
            # 接收客户端发送的消息
            data = await websocket.receive_text()
            if data.lower() == "ping":
                # 如果接收到的消息是 "ping"，则发送 "pong" 作为响应
                await websocket.send_text("pong")
            else:
                # 对于其他消息，发送提示信息
                await websocket.send_text("Please send 'ping' to get a 'pong' response.")
    except Exception as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        # 关闭 WebSocket 连接
        await websocket.close()