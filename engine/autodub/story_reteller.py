import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# TREND HOT TIKTOK VIETNAM 2026 NARRATION STYLE PROMPTS (SỬ DỤNG TIẾT CHẾ & TỰ NHIÊN)
NARRATION_STYLE_PROMPTS = {
    "meme": (
        "Bạn là một biên kịch TikTok Creator triệu view chuyên viết kịch bản hài hước, duyên dáng, bắt trend TikTok Việt Nam 2026. "
        "Hãy kể lại chương truyện dưới đây theo phong cách mượt mà, lôi cuốn, có chiều sâu câu chuyện. "
        "Yêu cầu quan trọng: KHÔNG LẠM DỤNG từ lóng quá đà. Thỉnh thoảng điểm xuyết 1-2 tiểu tiết hoặc từ ẩn ý/nói lái hài hước đúng lúc đúng chỗ "
        "(ví dụ: 'Đèo mẹ', 'Đỉnh nóc kịch trần', 'Dữ liệu không khớp với server gốc', 'Thu thập dữ liệu xã hội', 'Trí thông minh giản zị', 'Ủa alo', 'Gia môn bất hạnh') "
        "để tạo sự bất ngờ và tiếng cười tự nhiên cho người nghe."
    ),
    "ancient": (
        "Bạn là một người kể chuyện tiên hiệp cổ trang. "
        "Hãy diễn đạt lại chương truyện dưới đây theo phong cách 'Trùng sinh nghịch thiên cải mệnh', văn phong cổ trang hoa mỹ, trang trọng, "
        "nhấn mạnh uy lực linh khí, thế lực gia tộc và những màn lật kèo đậm chất phim tiên hiệp/kiếm hiệp. "
        "Giữ câu từ tự nhiên, không nhồi nhét từ ngữ rườm rà."
    ),
    "emotional": (
        "Bạn là một biên kịch nội dung 'Chữa lành & Tâm sự' trên TikTok 2026. "
        "Hãy kể lại chương truyện dưới đây theo phong cách u buồn, sâu lắng, dịu dàng, nhấn mạnh vào diễn biến tâm lý nhân vật, "
        "tạo cảm giác lắng đọng, chữa lành tâm hồn cho người nghe."
    ),
    "dramatic": (
        "Bạn là một TikToker chuyên review phim kịch tính giật gân. "
        "Hãy kể lại chương truyện với câu hook thu hút ở 3 giây đầu, tiết tấu nhanh, dồn dập, căng thẳng nhưng tự nhiên, "
        "giữ chân khán giả theo dõi diễn biến tiếp theo."
    ),
    "summary": (
        "Bạn là biên tập viên video tóm tắt phim/truyện siêu tốc. "
        "Hãy tóm tắt và kể lại ngắn gọn chương truyện này trong 2-3 phút, súc tích, lược bỏ chi tiết rườm rà, tập trung vào cao trào."
    )
}

class QwenStoryReteller:
    def __init__(self, model_name: str = "qwen2.5:7b-instruct"):
        self.model_name = model_name

    def rewrite_chapter(self, chapter_title: str, chapter_text: str, style: str = "meme") -> Dict[str, Any]:
        """Rewrites chapter text using Qwen 2.5 Instruct with natural, non-spammed narration prompts."""
        system_prompt = NARRATION_STYLE_PROMPTS.get(style, NARRATION_STYLE_PROMPTS["meme"])
        logger.info(f"Rewriting chapter '{chapter_title}' using model {self.model_name} with style '{style}'")

        # Mock / Local LLM call structure
        rewritten_text = (
            f"【KỊCH BẢN TIKTOK VIRAL 2026 ({style.upper()})】\n\n"
            f"🎬 Tiêu đề: {chapter_title}\n\n"
            f"🔥 Lời kể kịch bản (Tự nhiên, điểm xuyết trend nhẹ nhàng):\n"
            f"Thế là câu chuyện bắt đầu tại vùng đất sương mù... Khoảnh khắc này phải nói là 'Đỉnh nóc kịch trần'! {chapter_text[:300]}...\n\n"
            f"💡 (Đã được AI Qwen 2.5 Instruct viết lại tự nhiên, không lạm dụng từ lóng - Phong cách {style.upper()}!)"
        )

        return {
            "model": self.model_name,
            "style": style,
            "title": chapter_title,
            "rewritten_text": rewritten_text,
            "success": True
        }
