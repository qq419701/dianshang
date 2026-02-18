# -*- coding: utf-8 -*-
"""
==============================================
  通知服务
  功能：邮件、Webhook、站内信统一发送
==============================================
"""

import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from app import db
from app.models.notification import Notification, NotificationConfig, NotificationLog
from app.models.user import User
from config import Config

logger = logging.getLogger(__name__)


# 通知场景常量
SCENE_ORDER_CREATE = "order_create"
SCENE_ORDER_SUCCESS = "order_success"
SCENE_ORDER_FAIL = "order_fail"
SCENE_CONFIG_CHANGE = "config_change"
SCENE_LOGIN_ALERT = "login_alert"


def send_notification(merchant_id, scene, title, content, related_type="", related_id=None, user_ids=None):
    """
    发送通知（根据配置发送到多个渠道）
    
    参数：
        merchant_id: 商户ID
        scene: 通知场景
        title: 标题
        content: 内容
        related_type: 关联类型
        related_id: 关联ID
        user_ids: 接收用户ID列表（站内信）
    """
    try:
        # 查询通知配置
        configs = NotificationConfig.query.filter_by(
            merchant_id=merchant_id,
            scene=scene
        ).all()
        
        if not configs:
            logger.info(f"商户 {merchant_id} 场景 {scene} 未配置通知")
            return
        
        for config in configs:
            # 检查是否启用
            if hasattr(config, 'is_enabled') and not config.is_enabled:
                continue
                
            # 检查触发事件
            if hasattr(config, 'trigger_events') and config.trigger_events:
                if scene not in config.trigger_events:
                    continue
            
            # 发送邮件
            if config.enable_email and config.email_to:
                send_email(
                    merchant_id=merchant_id,
                    scene=scene,
                    to_addresses=config.email_to,
                    title=title,
                    content=content
                )
            
            # 发送钉钉机器人
            if hasattr(config, 'notify_type') and config.notify_type == 1 and config.webhook_url:
                send_dingtalk(
                    merchant_id=merchant_id,
                    scene=scene,
                    webhook_url=config.webhook_url,
                    secret=getattr(config, 'secret', None),
                    at_mobiles=getattr(config, 'at_mobiles', None),
                    title=title,
                    content=content
                )
            
            # 发送企业微信机器人
            elif hasattr(config, 'notify_type') and config.notify_type == 2 and config.webhook_url:
                send_wechat_work(
                    merchant_id=merchant_id,
                    scene=scene,
                    webhook_url=config.webhook_url,
                    mentioned_mobiles=getattr(config, 'at_mobiles', None),
                    title=title,
                    content=content
                )
            
            # 发送普通Webhook
            elif config.enable_webhook and config.webhook_url:
                send_webhook(
                    merchant_id=merchant_id,
                    scene=scene,
                    webhook_url=config.webhook_url,
                    title=title,
                    content=content,
                    related_type=related_type,
                    related_id=related_id
                )
            
            # 发送站内信
            if config.enable_site_msg and user_ids:
                send_site_message(
                    merchant_id=merchant_id,
                    scene=scene,
                    user_ids=user_ids,
                    title=title,
                    content=content,
                    related_type=related_type,
                    related_id=related_id
                )
            
    except Exception as e:
        logger.exception(f"发送通知失败：merchant_id={merchant_id}, scene={scene}")


def send_email(merchant_id, scene, to_addresses, title, content):
    """
    发送邮件通知
    
    参数：
        merchant_id: 商户ID
        scene: 通知场景
        to_addresses: 接收邮箱（多个用逗号分隔）
        title: 标题
        content: 内容
    """
    try:
        # 读取邮件配置
        smtp_server = getattr(Config, "SMTP_SERVER", None)
        smtp_port = getattr(Config, "SMTP_PORT", 465)
        smtp_user = getattr(Config, "SMTP_USER", None)
        smtp_password = getattr(Config, "SMTP_PASSWORD", None)
        smtp_from = getattr(Config, "SMTP_FROM", smtp_user)
        
        if not all([smtp_server, smtp_user, smtp_password]):
            logger.warning("邮件配置不完整，跳过发送")
            return
        
        # 解析接收人列表
        to_list = [addr.strip() for addr in to_addresses.split(",") if addr.strip()]
        if not to_list:
            logger.warning("收件人列表为空")
            return
        
        # 构建邮件
        msg = MIMEMultipart()
        msg["From"] = smtp_from
        msg["To"] = ", ".join(to_list)
        msg["Subject"] = title
        
        # HTML格式内容
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">
                    {title}
                </h2>
                <div style="margin-top: 20px;">
                    {content}
                </div>
                <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 12px; margin-top: 10px;">
                    这是一封系统自动发送的邮件，请勿直接回复。
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        # 发送邮件
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        # 记录日志
        log_notification(
            merchant_id=merchant_id,
            scene=scene,
            channel="email",
            to_address=to_addresses,
            title=title,
            content=content,
            status=1
        )
        
        logger.info(f"邮件发送成功：{to_addresses}")
        
    except Exception as e:
        logger.exception(f"邮件发送失败：{to_addresses}")
        log_notification(
            merchant_id=merchant_id,
            scene=scene,
            channel="email",
            to_address=to_addresses,
            title=title,
            content=content,
            status=0,
            error_message=str(e)
        )


def send_webhook(merchant_id, scene, webhook_url, title, content, related_type="", related_id=None):
    """
    发送Webhook通知
    
    参数：
        merchant_id: 商户ID
        scene: 通知场景
        webhook_url: Webhook地址
        title: 标题
        content: 内容
        related_type: 关联类型
        related_id: 关联ID
    """
    try:
        # 构建请求数据
        data = {
            "merchant_id": merchant_id,
            "scene": scene,
            "title": title,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if related_type:
            data["related_type"] = related_type
        if related_id:
            data["related_id"] = related_id
        
        # 发送POST请求
        response = requests.post(
            webhook_url,
            json=data,
            timeout=10
        )
        
        # 检查响应
        if response.status_code == 200:
            log_notification(
                merchant_id=merchant_id,
                scene=scene,
                channel="webhook",
                to_address=webhook_url,
                title=title,
                content=content,
                status=1
            )
            logger.info(f"Webhook发送成功：{webhook_url}")
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        
    except Exception as e:
        logger.exception(f"Webhook发送失败：{webhook_url}")
        log_notification(
            merchant_id=merchant_id,
            scene=scene,
            channel="webhook",
            to_address=webhook_url,
            title=title,
            content=content,
            status=0,
            error_message=str(e)
        )


def send_site_message(merchant_id, scene, user_ids, title, content, related_type="", related_id=None):
    """
    发送站内消息
    
    参数：
        merchant_id: 商户ID
        scene: 通知场景
        user_ids: 接收用户ID列表
        title: 标题
        content: 内容
        related_type: 关联类型
        related_id: 关联ID
    """
    try:
        # 确定消息类型
        type_map = {
            SCENE_ORDER_CREATE: 2,
            SCENE_ORDER_SUCCESS: 2,
            SCENE_ORDER_FAIL: 2,
            SCENE_CONFIG_CHANGE: 3,
            SCENE_LOGIN_ALERT: 4
        }
        msg_type = type_map.get(scene, 1)
        
        # 批量创建站内消息
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                title=title,
                content=content,
                type=msg_type,
                related_type=related_type,
                related_id=related_id,
                is_read=0
            )
            db.session.add(notification)
        
        db.session.commit()
        
        # 记录日志
        log_notification(
            merchant_id=merchant_id,
            scene=scene,
            channel="site_msg",
            to_address=f"user_ids={user_ids}",
            title=title,
            content=content,
            status=1
        )
        
        logger.info(f"站内消息发送成功：{len(user_ids)} 个用户")
        
    except Exception as e:
        logger.exception("站内消息发送失败")
        db.session.rollback()
        log_notification(
            merchant_id=merchant_id,
            scene=scene,
            channel="site_msg",
            to_address=f"user_ids={user_ids}",
            title=title,
            content=content,
            status=0,
            error_message=str(e)
        )


def log_notification(merchant_id, scene, channel, to_address, title, content, status, error_message=""):
    """
    记录通知日志
    """
    try:
        log = NotificationLog(
            merchant_id=merchant_id,
            scene=scene,
            channel=channel,
            to_address=to_address,
            title=title,
            content=content[:1000],  # 限制长度
            status=status,
            error_message=error_message
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.exception("记录通知日志失败")
        db.session.rollback()


def get_unread_count(user_id):
    """
    获取用户未读消息数量
    
    参数：
        user_id: 用户ID
    
    返回：
        int
    """
    try:
        count = Notification.query.filter_by(
            user_id=user_id,
            is_read=0
        ).count()
        return count
    except Exception:
        return 0


def send_dingtalk(merchant_id, scene, webhook_url, secret, at_mobiles, title, content):
    """
    发送钉钉机器人通知
    
    参数：
        merchant_id: 商户ID
        scene: 通知场景
        webhook_url: 钉钉机器人Webhook地址
        secret: 加签密钥
        at_mobiles: @ 的手机号列表
        title: 标题
        content: 内容
    """
    try:
        import time
        import hmac
        import hashlib
        import base64
        import urllib.parse
        
        # 如果有加签密钥，生成签名
        if secret:
            timestamp = str(round(time.time() * 1000))
            secret_enc = secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(timestamp, secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
        
        # 构建消息体
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"### {title}\n\n{content}"
            }
        }
        
        # 添加@功能
        if at_mobiles:
            data["at"] = {
                "atMobiles": at_mobiles if isinstance(at_mobiles, list) else [],
                "isAtAll": False
            }
        
        # 发送请求
        response = requests.post(webhook_url, json=data, timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            log_notification(
                merchant_id=merchant_id,
                scene=scene,
                channel="dingtalk",
                to_address=webhook_url,
                title=title,
                content=content,
                status=1
            )
            logger.info(f"钉钉通知发送成功")
        else:
            raise Exception(f"钉钉返回错误: {result.get('errmsg')}")
            
    except Exception as e:
        logger.exception(f"钉钉通知发送失败")
        log_notification(
            merchant_id=merchant_id,
            scene=scene,
            channel="dingtalk",
            to_address=webhook_url,
            title=title,
            content=content,
            status=0,
            error_message=str(e)
        )


def send_wechat_work(merchant_id, scene, webhook_url, mentioned_mobiles, title, content):
    """
    发送企业微信机器人通知
    
    参数：
        merchant_id: 商户ID
        scene: 通知场景
        webhook_url: 企业微信机器人Webhook地址
        mentioned_mobiles: @ 的手机号列表
        title: 标题
        content: 内容
    """
    try:
        # 构建消息体
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"**{title}**\n\n{content}"
            }
        }
        
        # 添加@功能
        if mentioned_mobiles:
            if isinstance(mentioned_mobiles, list) and mentioned_mobiles:
                data["markdown"]["mentioned_mobile_list"] = mentioned_mobiles
        
        # 发送请求
        response = requests.post(webhook_url, json=data, timeout=10)
        result = response.json()
        
        if result.get('errcode') == 0:
            log_notification(
                merchant_id=merchant_id,
                scene=scene,
                channel="wechat_work",
                to_address=webhook_url,
                title=title,
                content=content,
                status=1
            )
            logger.info(f"企业微信通知发送成功")
        else:
            raise Exception(f"企业微信返回错误: {result.get('errmsg')}")
            
    except Exception as e:
        logger.exception(f"企业微信通知发送失败")
        log_notification(
            merchant_id=merchant_id,
            scene=scene,
            channel="wechat_work",
            to_address=webhook_url,
            title=title,
            content=content,
            status=0,
            error_message=str(e)
        )
