"""
创建应用图标
生成一个简洁的文档管理器图标
"""
from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    """创建应用图标"""
    
    # 创建 256x256 的图标
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 背景色 - 深蓝色
    bg_color = (41, 98, 255)
    
    # 绘制圆角矩形背景
    corner_radius = 40
    draw.rounded_rectangle(
        [(0, 0), (size, size)],
        radius=corner_radius,
        fill=bg_color
    )
    
    # 绘制文档图标
    doc_color = (255, 255, 255)
    doc_margin = 50
    doc_width = size - 2 * doc_margin
    doc_height = size - 2 * doc_margin
    
    # 文档主体
    doc_x1 = doc_margin
    doc_y1 = doc_margin + 20
    doc_x2 = doc_margin + doc_width
    doc_y2 = doc_margin + doc_height
    
    # 绘制文档形状（带折角的纸张）
    fold_size = 50
    
    # 文档主体矩形
    draw.rectangle(
        [(doc_x1, doc_y1 + fold_size), (doc_x2, doc_y2)],
        fill=doc_color
    )
    
    # 文档上半部分（带折角）
    draw.polygon([
        (doc_x1, doc_y1 + fold_size),
        (doc_x1, doc_y1),
        (doc_x2 - fold_size, doc_y1),
        (doc_x2, doc_y1 + fold_size),
        (doc_x2, doc_y1 + fold_size),
    ], fill=doc_color)
    
    # 绘制折角三角形
    draw.polygon([
        (doc_x2 - fold_size, doc_y1),
        (doc_x2, doc_y1),
        (doc_x2, doc_y1 + fold_size),
    ], fill=(230, 230, 230))
    
    # 绘制几条横线表示文档内容
    line_color = (200, 200, 200)
    line_margin = doc_x1 + 30
    line_width = doc_width - 60
    line_y_start = doc_y1 + fold_size + 40
    line_height = 20
    line_spacing = 30
    
    for i in range(5):
        y = line_y_start + i * line_spacing
        draw.rectangle(
            [(line_margin, y), (line_margin + line_width, y + line_height)],
            fill=line_color
        )
    
    # 保存为 PNG
    png_path = 'assets/icons/app_icon.png'
    img.save(png_path)
    print(f"✓ 创建 PNG 图标: {png_path}")
    
    # 保存为 ICO (Windows 图标)
    ico_path = 'assets/icons/app.ico'
    
    # 创建多个尺寸的图标
    sizes = [16, 32, 48, 64, 128, 256]
    icons = []
    
    for s in sizes:
        icon_img = img.resize((s, s), Image.Resampling.LANCZOS)
        icons.append(icon_img)
    
    # 保存为 ICO 文件
    icons[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=icons[1:]
    )
    print(f"✓ 创建 ICO 图标: {ico_path}")
    
    return ico_path, png_path


if __name__ == "__main__":
    print("=" * 50)
    print("创建 DocManager 应用图标")
    print("=" * 50)
    
    try:
        ico_path, png_path = create_icon()
        print("\n✓ 图标创建完成!")
        print(f"  ICO: {ico_path}")
        print(f"  PNG: {png_path}")
    except Exception as e:
        print(f"\n✗ 创建失败: {e}")
        import traceback
        traceback.print_exc()
