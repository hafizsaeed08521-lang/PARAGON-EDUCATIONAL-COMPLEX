document.getElementById('admissions-form').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const form = e.target;
  const data = Object.fromEntries(new FormData(form).entries());
  const status = document.getElementById('form-status');
  status.textContent = 'Sending...';
  try{
    const res = await fetch('/api/apply',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(data)
    });
    const body = await res.json();
    if(res.ok){
      status.textContent = 'Application submitted — thank you!';
      form.reset();
    } else {
      status.textContent = body.error || 'Submission failed';
    }
  }catch(err){
    status.textContent = 'Network error — please try again';
  }
});
