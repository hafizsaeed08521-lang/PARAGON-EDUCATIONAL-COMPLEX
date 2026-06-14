const boardingFields = document.querySelector('.boarding-fields');
const admissionType = document.querySelector('[name="admissionType"]');

const classLevel = document.getElementById('classLevel');
const classChoice = document.getElementById('classChoice');
const hasMedical = document.getElementById('hasMedical');
const medicalFields = document.querySelector('.medical-fields');

const classMap = {
  preschool: [
    {value: 'crecheA', text: 'Creche A'},
    {value: 'crecheB', text: 'Creche B'},
    {value: 'kg1a', text: 'Kindergarten 1A'},
    {value: 'kg1b', text: 'Kindergarten 1B'},
    {value: 'kg2a', text: 'Kindergarten 2A'},
    {value: 'kg2b', text: 'Kindergarten 2B'}
  ],
  primary: [
    {value: 'bs1a', text: 'BS 1A'},
    {value: 'bs1b', text: 'BS 1B'},
    {value: 'bs2a', text: 'BS 2A'},
    {value: 'bs2b', text: 'BS 2B'},
    {value: 'bs3a', text: 'BS 3A'},
    {value: 'bs3b', text: 'BS 3B'},
    {value: 'bs4a', text: 'BS 4A'},
    {value: 'bs4b', text: 'BS 4B'},
    {value: 'bs5a', text: 'BS 5A'},
    {value: 'bs5b', text: 'BS 5B'},
    {value: 'bs6a', text: 'BS 6A'},
    {value: 'bs6b', text: 'BS 6B'}
  ],
  jhs: [
    {value: 'jhs1a', text: 'JHS 1A'},
    {value: 'jhs1b', text: 'JHS 1B'},
    {value: 'jhs2a', text: 'JHS 2A'},
    {value: 'jhs2b', text: 'JHS 2B'},
    {value: 'jhs3a', text: 'JHS 3A'},
    {value: 'jhs3b', text: 'JHS 3B'}
  ]
};

function populateClassChoices(level){
  classChoice.innerHTML = '<option value="">Select class...</option>';
  if(!level || !classMap[level]){
    classChoice.disabled = true;
    classChoice.required = false;
    return;
  }
  classMap[level].forEach(opt => {
    const el = document.createElement('option');
    el.value = opt.value;
    el.textContent = opt.text;
    classChoice.appendChild(el);
  });
  classChoice.disabled = false;
  classChoice.required = true;
}

if(classLevel){
  classLevel.addEventListener('change', ()=> populateClassChoices(classLevel.value));
  // initialize if form was prefilled
  populateClassChoices(classLevel.value);
}

if(hasMedical){
  hasMedical.addEventListener('change', ()=>{
    medicalFields.style.display = hasMedical.checked ? 'flex' : 'none';
  });
}

admissionType.addEventListener('change', ()=>{
  boardingFields.style.display = admissionType.value === 'boarding' ? 'flex' : 'none';
});

document.getElementById('admissions-form').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const status = document.getElementById('form-status');
  status.textContent = 'Sending...';
  try{
    const res = await fetch('/api/apply',{ 
      method:'POST',
      body: formData
    });
    const body = await res.json();
    if(res.ok){
      status.textContent = 'Application submitted — thank you!';
      form.reset();
      boardingFields.style.display = 'none';
      if(medicalFields) medicalFields.style.display = 'none';
    } else {
      status.textContent = body.error || 'Submission failed';
    }
  }catch(err){
    status.textContent = 'Network error — please try again';
  }
});
