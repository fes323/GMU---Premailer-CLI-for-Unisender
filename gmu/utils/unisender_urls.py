def build_unisender_message_url(message_id: int | str) -> str:
    return (
        "https://app.unisender.com/ru/v5/spa/email-campaign/editor/"
        f"{message_id}?isEmbedded=true&step=send"
    )
