import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from autodub.story_importer import TextCleaner

SAMPLE_WEBNOVEL_VN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Chương 10: Tham Sân yêu quỷ 2 - Cẩu Thả Thành Thánh Nhân | Webnovel.vn</title></head>
<body>
<div class="header-nav">
<span>×</span>
<a href="#">Tài khoản</a>
</div>

<div id="chapter-c" class="chapter-c">
<p>Mãi đến khi trời sáng, Cố An mới bắt đầu ngủ.</p>
<p>Năm ngày tiếp theo, Tham Sân yêu quỷ vẫn không xuất hiện, trái tim căng thẳng của Cố An dần dần thả lỏng.</p>
<p>Ngày thứ sáu.</p>
<p>Cố An vẫn như cũ, trời tối là về phòng nghỉ ngơi.</p>
<p>Thái Huyền môn không an toàn chút nào!</p>
</div>

<div class="chapter-nav">
<a href="#">Chương trước</a>
<a href="#">Chương sau</a>
<a href="#">Báo lỗi chương</a>
</div>

<div class="recommend">
📚 Tuyển tập truyện chọn lọc🔥 Top Truyện full hay nhất hiện nay➜⚔️ List truyện tiên hiệp chọn lọc nên đọc➜
</div>

<div class="reading-toolbar">
Bảng tác vụ đọc✕
Ds Chương
Cấu hình
Màu nền
Font chữ
−
+
Kiểu chữ
Palatino
Bookerly
Be Vietnam
Khôi phục mặc định
</div>
</body>
</html>
"""

class TestTextCleaner(unittest.TestCase):
    def test_clean_html_webnovel_vn(self):
        cleaned = TextCleaner.clean_html_content(SAMPLE_WEBNOVEL_VN_HTML)
        self.assertIn("Mãi đến khi trời sáng, Cố An mới bắt đầu ngủ.", cleaned)
        self.assertIn("Thái Huyền môn không an toàn chút nào!", cleaned)
        
        # Verify website chrome/junk is completely removed
        self.assertNotIn("Tài khoản", cleaned)
        self.assertNotIn("Báo lỗi chương", cleaned)
        self.assertNotIn("Chương trước", cleaned)
        self.assertNotIn("Chương sau", cleaned)
        self.assertNotIn("Tuyển tập truyện chọn lọc", cleaned)
        self.assertNotIn("Palatino", cleaned)
        self.assertNotIn("Khôi phục mặc định", cleaned)
        self.assertNotIn("Bảng tác vụ đọc", cleaned)

    def test_clean_raw_text_with_junk(self):
        raw_text = """Chương 10: Tham Sân yêu quỷ 2 | Webnovel.vn
×
Tài khoản

Mãi đến khi trời sáng, Cố An mới bắt đầu ngủ.

Chương trước
Báo lỗi chương
Ds Chương
Bookerly
Khôi phục mặc định"""
        cleaned = TextCleaner.clean_html_content(raw_text)
        self.assertIn("Mãi đến khi trời sáng, Cố An mới bắt đầu ngủ.", cleaned)
        self.assertNotIn("Tài khoản", cleaned)
        self.assertNotIn("Báo lỗi chương", cleaned)
        self.assertNotIn("Bookerly", cleaned)

if __name__ == "__main__":
    unittest.main()
