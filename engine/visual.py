"""Görsel regresyon: iki ekran görüntüsünü piksel piksel karşılaştırır.

Yöntem (bilerek basit tutuldu):
  1. İki görüntünün boyutu aynı olmalı.
  2. Her pikselde renk farkı hesaplanır (Pillow ImageChops.difference).
  3. Farkı TOLERANCE'tan büyük olan pikseller "değişmiş" sayılır. Küçük tolerans, aynı sayfanın
     iki çiziminde oluşabilecek gözle görülmeyen renk oynamalarını yok sayar.
  4. Değişen piksellerin oranı izin verilen yüzdeyi aşarsa test kalır.
  5. Fark görüntüsü: gerçek görüntünün soluk hâli üzerinde değişen pikseller kırmızı.
"""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops

TOLERANCE = 16  # 0-255 arası; bundan küçük renk farkları yok sayılır
MAX_DIFF_PERCENT = 0.01  # değişen piksel oranı bu yüzdeyi aşarsa kalır (%0,01 ≈ 1280x720'de 92 piksel)


@dataclass
class VisualDiff:
    changed_pixels: int
    total_pixels: int
    same_size: bool

    @property
    def percent(self) -> float:
        return 100 * self.changed_pixels / self.total_pixels if self.total_pixels else 0.0

    @property
    def passed(self) -> bool:
        return self.same_size and self.percent <= MAX_DIFF_PERCENT


def compare_images(baseline: Path, actual: Path, diff_out: Path) -> VisualDiff:
    """İki PNG'yi karşılaştırır, fark görüntüsünü diff_out'a yazar."""
    base = Image.open(baseline).convert("RGB")
    act = Image.open(actual).convert("RGB")

    if base.size != act.size:
        act.save(diff_out)  # boyut farklıysa piksel karşılaştırması anlamsız
        return VisualDiff(changed_pixels=0, total_pixels=0, same_size=False)

    # Her piksel için en büyük kanal farkı (R, G, B) -> tek kanallı gri görüntü
    r, g, b = ImageChops.difference(base, act).split()
    strongest = ImageChops.lighter(ImageChops.lighter(r, g), b)  # lighter = piksel piksel en büyüğü
    mask = strongest.point(lambda value: 255 if value > TOLERANCE else 0)
    changed = mask.histogram()[255]

    # Fark görüntüsü: soluk gri arka plan + kırmızı değişen pikseller
    faded = Image.blend(act.convert("L").convert("RGB"), Image.new("RGB", act.size, "white"), 0.7)
    red = Image.new("RGB", act.size, (230, 20, 20))
    Image.composite(red, faded, mask).save(diff_out)

    return VisualDiff(changed_pixels=changed, total_pixels=act.size[0] * act.size[1], same_size=True)
