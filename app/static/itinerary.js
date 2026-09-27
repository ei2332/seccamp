const rows = document.querySelector('#itinerary-fields');
const template = document.querySelector('#step-template');
const add = document.querySelector('#add-step');
if (rows && template && add) {
  add.addEventListener('click', () => {
    if (rows.children.length >= 50) return;
    const fragment = template.content.cloneNode(true);
    const days = rows.querySelectorAll('[name="step_day"]');
    fragment.querySelector('[name="step_day"]').value = days.length ? days[days.length - 1].value : '1';
    rows.append(fragment);
    rows.lastElementChild.querySelector('[name="step_title"]').focus();
    add.disabled = rows.children.length >= 50;
  });
  rows.addEventListener('click', (event) => {
    if (!event.target.closest('.remove-step')) return;
    event.target.closest('.step-editor').remove();
    add.disabled = false;
    add.focus();
  });
}
