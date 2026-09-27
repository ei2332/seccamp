document.addEventListener('submit', async (event) => {
  const form = event.target.closest('[data-favorite-form]');
  if (!form) return;
  event.preventDefault();
  const button = form.querySelector('button');
  if (button.disabled) return;
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
  const status = document.querySelector('#favorite-status');
  status.textContent = '';
  try {
    const response = await fetch(form.getAttribute('action'), {
      method: 'POST', body: new FormData(form),
      headers: {Accept: 'application/json'}, credentials: 'same-origin'
    });
    if (!response.ok) throw new Error('request failed');
    const data = await response.json();
    if (typeof data.favorite !== 'boolean') throw new Error('invalid response');
    // 同じしおりが複数箇所にある場合も状態を揃える。
    document.querySelectorAll('[data-favorite-form]').forEach((other) => {
      if (other.getAttribute('action') !== form.getAttribute('action')) return;
      other.querySelector('[name="action"]').value = data.favorite ? 'remove' : 'add';
      const control = other.querySelector('button');
      control.setAttribute('aria-pressed', String(data.favorite));
      const label = data.favorite ? 'お気に入りから外す' : 'お気に入りに登録';
      control.title = label;
      const text = other.querySelector('[data-favorite-label]');
      if (text) text.textContent = label;
    });
    status.textContent = data.favorite ? 'お気に入りに登録しました。' : 'お気に入りを解除しました。';
  } catch {
    status.textContent = '変更を確認できませんでした。画面を再読み込みして状態を確認してください。';
  } finally {
    button.disabled = false;
    button.removeAttribute('aria-busy');
  }
});
