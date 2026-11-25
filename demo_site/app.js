// Mini Market — platformun canlı demosu için örnek mağaza.
// Sunucu tarafı yok: oturum ve sepet tarayıcının localStorage'ında tutulur.
// Her test yeni bir browser context'te koştuğu için testler birbirinin sepetini görmez.
//
// İKİ SÜRÜM: Aynı dosyalar iki adreste yayınlanır.
//   /demo/     -> Sürüm 1.0, doğru çalışır.
//   /demo-v2/  -> Sürüm 2.0, BİLEREK HATALI: sepette birden fazla ürün varsa toplam,
//                 son ürünü hesaba katmaz. Platformun bu "regresyonu" yakalaması gösterilir.

const MiniMarket = (() => {
  const IS_V2 = location.pathname.includes("/demo-v2");

  const PRODUCTS = [
    { id: "kulaklik", name: "Kablosuz Kulaklık", price: 1250 },
    { id: "klavye", name: "Mekanik Klavye", price: 2400 },
    { id: "fare", name: "Oyuncu Faresi", price: 850 },
    { id: "kablo", name: "USB-C Kablo", price: 150 },
  ];

  const USERS = { demo: "demo123", kilitli: "demo123" };

  // Gerçek bir sunucuyu taklit eden gecikmeler. Testler sabit beklemeyle değil,
  // Playwright'ın otomatik beklemesiyle bunları aşar.
  const LOGIN_DELAY_MS = 600;
  const PRODUCTS_DELAY_MS = 400;

  const $ = (sel) => document.querySelector(sel);
  const money = (n) => n.toLocaleString("tr-TR") + " TL";
  const getCart = () => JSON.parse(localStorage.getItem("sepet") || "{}");
  const saveCart = (cart) => localStorage.setItem("sepet", JSON.stringify(cart));
  const cartCount = (cart) => Object.values(cart).reduce((a, b) => a + b, 0);

  function showVersion() {
    $("[data-testid=surum]").textContent = IS_V2 ? "Sürüm 2.0 (yeni)" : "Sürüm 1.0";
  }

  function requireLogin() {
    if (!localStorage.getItem("kullanici")) location.href = "index.html";
  }

  function cartTotal(lines) {
    // lines: [{price, qty}, ...]
    let counted = lines;
    if (IS_V2 && lines.length > 1) {
      counted = lines.slice(0, -1); // BİLEREK KONULMUŞ HATA (sürüm 2.0)
    }
    return counted.reduce((sum, l) => sum + l.price * l.qty, 0);
  }

  function loginPage() {
    showVersion();
    const form = $("#giris-formu");
    const error = $("[data-testid=hata-mesaji]");
    const button = $("#giris-butonu");

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const user = $("#kullanici").value.trim();
      const pass = $("#sifre").value;
      error.hidden = true;

      if (!user) return showError("Kullanıcı adı zorunlu.");
      if (!pass) return showError("Şifre zorunlu.");

      button.disabled = true;
      button.textContent = "Giriş yapılıyor…";
      setTimeout(() => {
        button.disabled = false;
        button.textContent = "Giriş yap";
        if (USERS[user] !== pass) return showError("Kullanıcı adı veya şifre hatalı.");
        if (user === "kilitli") return showError("Bu hesap kilitlendi. Lütfen destek ile iletişime geçin.");
        localStorage.setItem("kullanici", user);
        location.href = "urunler.html";
      }, LOGIN_DELAY_MS);
    });

    function showError(msg) {
      error.textContent = msg;
      error.hidden = false;
    }
  }

  function productsPage() {
    requireLogin();
    showVersion();
    const badge = $("[data-testid=sepet-sayaci]");
    badge.textContent = cartCount(getCart());

    $("#cikis").addEventListener("click", () => {
      localStorage.clear();
      location.href = "index.html";
    });

    setTimeout(() => {
      $("#yukleniyor").remove();
      const grid = $("#urunler");
      for (const p of PRODUCTS) {
        const card = document.createElement("article");
        card.className = "urun";
        card.dataset.testid = "urun-" + p.id;
        card.innerHTML = `
          <h2>${p.name}</h2>
          <p class="fiyat">${money(p.price)}</p>
          <button type="button" data-testid="sepete-ekle-${p.id}">Sepete ekle</button>`;
        card.querySelector("button").addEventListener("click", (e) => {
          const cart = getCart();
          cart[p.id] = (cart[p.id] || 0) + 1;
          saveCart(cart);
          badge.textContent = cartCount(cart);
          e.target.textContent = "Eklendi ✓";
        });
        grid.appendChild(card);
      }
    }, PRODUCTS_DELAY_MS);
  }

  function cartPage() {
    requireLogin();
    showVersion();
    const cart = getCart();
    const lines = PRODUCTS.filter((p) => cart[p.id]).map((p) => ({ ...p, qty: cart[p.id] }));

    if (lines.length === 0) {
      $("#bos-sepet").hidden = false;
      $("#sepet-tablosu").hidden = true;
      $("#siparis-formu").hidden = true;
      return;
    }

    for (const l of lines) {
      const tr = document.createElement("tr");
      tr.dataset.testid = "sepet-satiri";
      tr.innerHTML = `<td>${l.name}</td><td>${l.qty}</td><td>${money(l.price * l.qty)}</td>`;
      $("#satirlar").appendChild(tr);
    }
    $("#toplam").textContent = money(cartTotal(lines));

    $("#siparis-formu").addEventListener("submit", (e) => {
      e.preventDefault();
      const err = $("[data-testid=form-hatasi]");
      if (!$("#ad").value.trim()) {
        err.textContent = "Ad soyad zorunlu.";
        err.hidden = false;
        return;
      }
      if (!$("#adres").value.trim()) {
        err.textContent = "Adres zorunlu.";
        err.hidden = false;
        return;
      }
      saveCart({});
      $("#siparis-no").textContent = "MM-" + Math.floor(100000 + Math.random() * 900000);
      $("#sepet-bolumu").hidden = true;
      $("#sonuc").hidden = false;
    });
  }

  return { loginPage, productsPage, cartPage };
})();
