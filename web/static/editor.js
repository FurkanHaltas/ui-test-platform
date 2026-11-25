// YAML editörü: yazarken canlı doğrulama + Tab ile girinti + Ctrl+S ile kaydet.
// Doğrulamayı sunucudaki /api/validate yapar; yani kurallar ve Türkçe mesajlar motorla aynı.
(() => {
  const textarea = document.getElementById("yaml");
  const box = document.getElementById("validation");
  const form = document.getElementById("editor-form");
  let timer = null;

  async function validate() {
    try {
      const res = await fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yaml: textarea.value }),
      });
      const data = await res.json();
      show(data);
    } catch {
      box.className = "validation";
      box.textContent = "Doğrulama yapılamadı (sunucuya ulaşılamadı).";
    }
  }

  function show(data) {
    box.replaceChildren();
    if (data.valid) {
      box.className = "validation is-valid";
      box.textContent = `✓ Geçerli · ${data.step_count} adım`;
      return;
    }
    box.className = "validation is-invalid";
    const title = document.createElement("strong");
    title.textContent = "Test tanımı geçersiz:";
    const list = document.createElement("ul");
    for (const err of data.errors) {
      const li = document.createElement("li");
      li.textContent = err; // textContent: kullanıcı metni HTML olarak yorumlanmaz
      list.appendChild(li);
    }
    box.append(title, list);
  }

  // Her tuşta değil, yazmayı 400 ms bırakınca doğrula (debounce).
  textarea.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(validate, 400);
  });

  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Tab" && !e.shiftKey) {
      // YAML sekme karakterine izin vermez; Tab iki boşluk eklesin.
      e.preventDefault();
      textarea.setRangeText("  ", textarea.selectionStart, textarea.selectionEnd, "end");
      textarea.dispatchEvent(new Event("input"));
    }
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  // Sayfa açılınca bir kez doğrula (sunucu zaten hata gösterdiyse onları koru).
  if (!box.classList.contains("is-invalid")) validate();
})();
