const API = 'http://localhost:3000';
let CURRENT_USER_ID = 1;
const CATEGORIES = ['All categories', 'Programming', 'Design', 'Writing', 'Tutoring'];
const PAYMENT_LABELS = { Paid: 'Paid', SkillSwap: 'Skill swap', Free: 'Free' };
const state = {
  view: 'discover', gigs: [], users: [], applications: [], reviews: [],
  search: '', category: 'All categories', type: 'All types', payment: 'All payment types',
  status: 'All statuses', minBudget: '', maxBudget: '', currentUser: null, selectedRating: 5
};
const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const initials = name => String(name || '?').trim().split(/\s+/).slice(0,2).map(p=>p[0]).join('').toUpperCase();
const avatarClass = id => ['avatar-purple','avatar-green','avatar-orange','avatar-blue','avatar-pink'][Number(id||1)%5];
const userById = id => state.users.find(u => Number(u.id) === Number(id));
const gigById = id => state.gigs.find(g => Number(g.id) === Number(id));
const money = n => n == null ? '' : `Rs. ${Number(n).toLocaleString('en-PK')}`;
const avgRating = userId => {
  const scores = state.reviews.filter(r => Number(r.reviewee_id) === Number(userId)).map(r=>Number(r.rating));
  return scores.length ? (scores.reduce((a,b)=>a+b,0)/scores.length).toFixed(1) : 'New';
};
const completedCount = userId => state.gigs.filter(g => Number(g.user_id)===Number(userId) && g.status==='Completed').length;
const statusClass = s => ({Open:'status-open','In Progress':'status-progress',Completed:'status-completed',Expired:'status-expired',Cancelled:'status-cancelled',Pending:'status-pending',Accepted:'status-accepted',Rejected:'status-rejected'}[s]||'status-expired');
const paymentClass = p => ({Paid:'payment-paid',SkillSwap:'payment-swap',Free:'payment-free'}[p]||'payment-free');
const paymentText = p => PAYMENT_LABELS[p] || p;
const isExpired = g => g.status === 'Open' && g.deadline && new Date(`${g.deadline}T23:59:59`) < new Date();
const displayStatus = g => isExpired(g) ? 'Expired' : g.status;
const canApply = g => Number(g.user_id)!==CURRENT_USER_ID && displayStatus(g)==='Open';
const canReview = g => g.status==='Completed' &&
  (Number(g.user_id)===CURRENT_USER_ID || Number(g.accepted_applicant_id)===CURRENT_USER_ID) &&
  !state.reviews.some(r=>Number(r.gig_id)===Number(g.id)&&Number(r.reviewer_id)===CURRENT_USER_ID);
const toast = (message, kind='') => {
  const root=$('#toastRoot'), node=document.createElement('div');
  node.className=`toast ${kind}`; node.textContent=message; root.append(node);
  setTimeout(()=>node.remove(),3200);
};
async function api(path, options={}) {
  const res=await fetch(`${API}${path}`,{headers:{'Content-Type':'application/json'},...options});
  if(!res.ok) { let msg=`Request failed (${res.status})`; try { const data=await res.json(); msg=data.message||msg; } catch{} throw new Error(msg); }
  if(res.status===204) return null;
  return res.json();
}
async function refreshData() {
  const [users,gigs,applications,reviews]=await Promise.all([
    api('/users'),api('/gigs'),api('/applications'),api('/reviews')
  ]);
  state.users=users; state.gigs=gigs; state.applications=applications; state.reviews=reviews;
  state.currentUser=userById(CURRENT_USER_ID);
  updateSidebar();
}
function updateSidebar(){
  const u=state.currentUser;if(!u)return;
  $('#sidebarAvatar').textContent=initials(u.name);$('#sidebarAvatar').className=`avatar ${avatarClass(u.id)}`;
  $('#sidebarName').textContent=u.name;$('#sidebarMajor').textContent=u.major;
  $('#myGigsCount').textContent=state.gigs.filter(g=>Number(g.user_id)===CURRENT_USER_ID).length;
  const switcher=$('#demoUserSwitch');
  if(switcher){switcher.innerHTML=state.users.map(person=>`<option value="${person.id}">${esc(person.name)}</option>`).join('');switcher.value=String(CURRENT_USER_ID);}
}
function navTo(view){
  state.view=view;
  $$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
  const labels={'discover':'Discover gigs','my-gigs':'My gigs','applications':'Applications','profile':'My profile'};
  $('#breadcrumbCurrent').textContent=labels[view]||'Discover gigs';
  render();
}
function render(){
  if(state.view==='discover') renderDiscover();
  else if(state.view==='my-gigs') renderMyGigs();
  else if(state.view==='applications') renderApplications();
  else if(state.view==='profile') renderProfile();
}
function hero(){
  return `<section class="hero"><div class="hero-copy"><div class="eyebrow"><span>✦</span> THE CAMPUS SKILL NETWORK</div><h1>Big skills start with <em>small opportunities.</em></h1><p>Find your people. Trade what you know. Get help with what you're learning. Your next opportunity is right here on campus.</p><div class="hero-actions"><button class="button button-primary" data-action="post">＋ Post a gig</button><button class="button button-secondary" data-action="how">How it works ↗</button></div></div><div class="hero-art" aria-hidden="true"><div class="art-card one"><div class="art-mini"><span class="art-icon">✳</span><span>Design a poster</span></div><div class="art-line"></div><div class="art-line short"></div><div class="art-tags"><span>Design</span><span>Paid</span></div></div><div class="art-card two"><div class="art-mini"><span class="art-icon">⌘</span><span>Java study buddy</span></div><div class="art-line"></div><div class="art-line short"></div><div class="art-tags"><span>Programming</span><span>Skill swap</span></div></div></div></section>`;
}
function stats(){
  const open=state.gigs.filter(g=>displayStatus(g)==='Open').length;
  const completed=state.gigs.filter(g=>g.status==='Completed').length;
  const swaps=state.gigs.filter(g=>g.payment_type==='SkillSwap').length;
  return `<div class="stats-row">
    <div class="stat-card"><div class="stat-icon purple">✦</div><div><div class="stat-number">${state.gigs.length}</div><div class="stat-label">Community gigs</div></div></div>
    <div class="stat-card"><div class="stat-icon green">↗</div><div><div class="stat-number">${open}</div><div class="stat-label">Open opportunities</div></div></div>
    <div class="stat-card"><div class="stat-icon amber">⇄</div><div><div class="stat-number">${swaps}</div><div class="stat-label">Skill swaps</div></div></div>
    <div class="stat-card"><div class="stat-icon blue">✓</div><div><div class="stat-number">${completed}</div><div class="stat-label">Gigs completed</div></div></div>
  </div>`;
}
function gigCard(g){
  const owner=userById(g.user_id)||{name:'Campus student',major:'MUET student',id:0};
  const mine=Number(g.user_id)===CURRENT_USER_ID;
  const app=state.applications.find(a=>Number(a.gig_id)===Number(g.id)&&Number(a.applicant_id)===CURRENT_USER_ID);
  const status=displayStatus(g);
  let action='';
  if(canApply(g)){
    action=app?`<button class="mini-btn" data-action="application-status" data-id="${g.id}">Application: ${esc(app.status)}</button>`:`<button class="mini-btn primary" data-action="apply" data-id="${g.id}">Apply ↗</button>`;
  } else if(mine && status==='Open') action=`<button class="mini-btn primary" data-action="manage-gig" data-id="${g.id}">Manage</button>`;
  else if(canReview(g)) action=`<button class="mini-btn primary" data-action="review" data-id="${g.id}">Leave review ★</button>`;
  else action=`<button class="mini-btn" data-action="details" data-id="${g.id}">Details ↗</button>`;
  const price=g.payment_type==='Paid'?money(g.budget):g.payment_type==='Free'?'No payment':'Skill exchange';
  return `<article class="gig-card">
    <div class="gig-top"><span class="category-label">${esc(g.category)}</span><span class="status-pill ${statusClass(status)}">${esc(status)}</span></div>
    <h3>${esc(g.title)}</h3><p class="gig-description">${esc(g.description)}</p>
    <div class="gig-meta"><span>◉ ${esc(g.type)}</span><span>◷ Due <b>${esc(g.deadline||'Flexible')}</b></span></div>
    <div class="gig-owner"><div class="avatar ${avatarClass(owner.id)}">${esc(initials(owner.name))}</div><div class="owner-info"><strong>${esc(owner.name)} ${mine?'<span style="color:#6b58d6">(You)</span>':''}</strong><span>${esc(owner.major||'MUET student')}</span></div><span class="rating-mini">★ ${avgRating(owner.id)}</span></div>
    <div class="gig-card-bottom"><div class="gig-price">${esc(price)}<small>${esc(paymentText(g.payment_type))}</small></div><div class="gig-actions">${action}<button class="mini-btn" data-action="details" data-id="${g.id}" aria-label="View gig details">↗</button></div></div>
  </article>`;
}
function emptyState(title,desc,button=''){
  return `<div class="empty-state"><div class="empty-icon">✳</div><h3>${esc(title)}</h3><p>${esc(desc)}</p>${button}</div>`;
}
function renderDiscover(){
  const query=state.search.trim().toLowerCase();
  const invalidBudget=state.minBudget!==''&&state.maxBudget!==''&&Number(state.minBudget)>Number(state.maxBudget);
  const gigs=state.gigs.filter(g=>{
    const qmatch=!query||`${g.title} ${g.description} ${g.category}`.toLowerCase().includes(query);
    const cmatch=state.category==='All categories'||g.category===state.category;
    const tmatch=state.type==='All types'||g.type===state.type;
    const pmatch=state.payment==='All payment types'||g.payment_type===state.payment;
    const smatch=state.status==='All statuses'||displayStatus(g)===state.status;
    const min=state.minBudget===''?null:Number(state.minBudget), max=state.maxBudget===''?null:Number(state.maxBudget);
    const hasBudgetFilter=min!==null||max!==null;
    const bmatch=!hasBudgetFilter||(g.payment_type==='Paid'&&(min===null||Number(g.budget)>=min)&&(max===null||Number(g.budget)<=max));
    return !invalidBudget&&qmatch&&cmatch&&tmatch&&pmatch&&smatch&&bmatch;
  }).sort((a,b)=>Number(displayStatus(a)!=='Open')-Number(displayStatus(b)!=='Open')||Number(b.id)-Number(a.id));
  $('#viewRoot').innerHTML=`${hero()}${stats()}
    <div class="section-head"><div><h2>Find your next opportunity</h2><p>Small gigs. Real skills. Better together.</p></div><button class="text-button" data-action="reset-filters">Reset filters ↺</button></div>
    <div class="toolbar"><div class="search-wrap"><span>⌕</span><input id="searchInput" class="field" placeholder="Search gigs, skills, or keywords..." value="${esc(state.search)}" aria-label="Search gigs"></div>
      <select id="categoryFilter" aria-label="Filter category">${CATEGORIES.map(c=>`<option ${state.category===c?'selected':''}>${esc(c)}</option>`).join('')}</select>
      <select id="typeFilter" aria-label="Filter gig type">${['All types','Offering','Requesting'].map(c=>`<option ${state.type===c?'selected':''}>${esc(c)}</option>`).join('')}</select>
      <select id="paymentFilter" aria-label="Filter payment type">${['All payment types','Paid','SkillSwap','Free'].map(c=>`<option value="${esc(c)}" ${state.payment===c?'selected':''}>${esc(c==='SkillSwap'?'Skill swap':c)}</option>`).join('')}</select>
      <div class="budget-filter" aria-label="Filter paid gigs by budget range"><span>Budget (Rs.)</span><input id="minBudgetFilter" type="number" min="0" placeholder="Min" aria-label="Minimum budget" value="${esc(state.minBudget)}"><span class="budget-dash">–</span><input id="maxBudgetFilter" type="number" min="0" placeholder="Max" aria-label="Maximum budget" value="${esc(state.maxBudget)}"></div>
    </div>
    <div class="filter-tabs">${['All statuses','Open','In Progress','Completed','Expired','Cancelled'].map(s=>`<button class="filter-chip ${state.status===s?'active':''}" data-action="status-filter" data-status="${esc(s)}">${esc(s)}</button>`).join('')}</div>
    <div class="section-head"><div><h2>${gigs.length===state.gigs.length?'Latest campus gigs':`${gigs.length} matching gig${gigs.length===1?'':'s'}`}</h2><p>Browse student-created opportunities around MUET.</p>${invalidBudget?'<p class="filter-error">Minimum budget must be less than or equal to maximum budget.</p>':''}</div><span class="api-badge">● LIVE MOCK API</span></div>
    <div class="gig-grid">${gigs.length?gigs.map(gigCard).join(''):emptyState('No gigs found','Try changing your search or filters.','<button class="button button-secondary" data-action="reset-filters">Clear filters</button>')}</div>`;
  $('#searchInput').addEventListener('input',e=>{state.search=e.target.value;renderDiscoverPreserveFocus(e.target.selectionStart);});
  $('#categoryFilter').addEventListener('change',e=>{state.category=e.target.value;renderDiscover();});
  $('#typeFilter').addEventListener('change',e=>{state.type=e.target.value;renderDiscover();});
  $('#paymentFilter').addEventListener('change',e=>{state.payment=e.target.value;renderDiscover();});
  $('#minBudgetFilter').addEventListener('change',e=>{state.minBudget=e.target.value;renderDiscover();});
  $('#maxBudgetFilter').addEventListener('change',e=>{state.maxBudget=e.target.value;renderDiscover();});
}
function renderDiscoverPreserveFocus(pos){
  const old=$('#searchInput');if(!old)return;
  // Update only the cards and result headings while keeping the input cursor stable.
  const root=$('#viewRoot');
  const active=old; const value=state.search;
  renderDiscover();
  const next=$('#searchInput');next.focus();next.setSelectionRange(pos,pos);
}
function renderMyGigs(){
  const mine=state.gigs.filter(g=>Number(g.user_id)===CURRENT_USER_ID).sort((a,b)=>Number(b.id)-Number(a.id));
  const open=mine.filter(g=>displayStatus(g)==='Open').length, progress=mine.filter(g=>g.status==='In Progress').length, done=mine.filter(g=>g.status==='Completed').length;
  $('#viewRoot').innerHTML=`<div class="page-heading"><div><div class="eyebrow">YOUR WORKSPACE</div><h1>My gigs</h1><p>Keep track of opportunities you've posted and manage the students who apply.</p></div><button class="button button-primary" data-action="post">＋ Create a gig</button></div>
  <div class="stats-row"><div class="stat-card"><div class="stat-icon purple">▤</div><div><div class="stat-number">${mine.length}</div><div class="stat-label">Total posted</div></div></div><div class="stat-card"><div class="stat-icon green">●</div><div><div class="stat-number">${open}</div><div class="stat-label">Open</div></div></div><div class="stat-card"><div class="stat-icon amber">↻</div><div><div class="stat-number">${progress}</div><div class="stat-label">In progress</div></div></div><div class="stat-card"><div class="stat-icon blue">✓</div><div><div class="stat-number">${done}</div><div class="stat-label">Completed</div></div></div></div>
  <div class="panel"><div class="panel-title"><h3>Posted by you</h3><span>${mine.length} gigs</span></div><div class="stack-list">${mine.length?mine.map(g=>{
    const apps=state.applications.filter(a=>Number(a.gig_id)===Number(g.id));
    const status=displayStatus(g);
    return `<div class="list-row"><div class="stat-icon purple">${g.type==='Offering'?'✦':'⌕'}</div><div class="row-info"><strong>${esc(g.title)}</strong><span>${esc(g.category)} · ${esc(paymentText(g.payment_type))} · ${apps.length} application${apps.length===1?'':'s'} · Due ${esc(g.deadline)}</span></div><span class="status-pill ${statusClass(status)}">${esc(status)}</span><div class="row-actions"><button class="mini-btn" data-action="details" data-id="${g.id}">View</button>${status==='Open'?`<button class="mini-btn primary" data-action="manage-gig" data-id="${g.id}">Manage</button>`:''}${status==='In Progress'?`<button class="mini-btn primary" data-action="complete-gig" data-id="${g.id}">Mark completed</button>`:''}${canReview(g)?`<button class="mini-btn primary" data-action="review" data-id="${g.id}">Leave review ★</button>`:''}</div></div>`;
  }).join(''):emptyState('No gigs posted yet','Create a gig to find collaborators or offer a skill.','<button class="button button-primary" data-action="post">＋ Post your first gig</button>')}</div></div>`;
}
function renderApplications(){
  const mine=state.applications.filter(a=>Number(a.applicant_id)===CURRENT_USER_ID).sort((a,b)=>Number(b.id)-Number(a.id));
  const incoming=state.gigs.filter(g=>Number(g.user_id)===CURRENT_USER_ID).flatMap(g=>state.applications.filter(a=>Number(a.gig_id)===Number(g.id)).map(a=>({...a,gig:g,incoming:true}))).sort((a,b)=>Number(b.id)-Number(a.id));
  const row=(a,incomingMode=false)=>{
    const g=a.gig||gigById(a.gig_id), person=userById(incomingMode?a.applicant_id:g?.user_id);
    if(!g)return '';
    return `<div class="list-row"><div class="avatar ${avatarClass(person?.id)}">${esc(initials(person?.name))}</div><div class="row-info"><strong>${esc(g.title)}</strong><span>${incomingMode?`Applicant: ${esc(person?.name||'Student')}`:`Posted by ${esc(person?.name||'Student')}`} · ${esc(a.message)}</span></div><span class="status-pill ${statusClass(a.status)}">${esc(a.status)}</span><div class="row-actions">${incomingMode&&a.status==='Pending'&&displayStatus(g)==='Open'?`<button class="mini-btn primary" data-action="accept-app" data-id="${a.id}">Accept</button><button class="mini-btn" data-action="reject-app" data-id="${a.id}">Reject</button>`:''}<button class="mini-btn" data-action="details" data-id="${g.id}">Gig details</button></div></div>`;
  };
  $('#viewRoot').innerHTML=`<div class="page-heading"><div><div class="eyebrow">KEEP THINGS MOVING</div><h1>Applications</h1><p>Track the gigs you've applied for and review students interested in your posts.</p></div><span class="api-badge">● API CONNECTED</span></div>
  <div class="two-col"><section class="panel"><div class="panel-title"><h3>Applications you've sent</h3><span>${mine.length} total</span></div><div class="stack-list">${mine.length?mine.map(a=>row(a,false)).join(''):emptyState('No applications yet','Find an open gig and send a short introduction.')}</div></section>
  <section class="panel"><div class="panel-title"><h3>Incoming applications</h3><span>${incoming.length} total</span></div><div class="stack-list">${incoming.length?incoming.map(a=>row(a,true)).join(''):emptyState('Nothing to review yet','Applications to your gigs will appear here.')}</div></section></div>`;
}
function renderProfile(){
  const u=state.currentUser, mine=state.gigs.filter(g=>Number(g.user_id)===CURRENT_USER_ID), userReviews=state.reviews.filter(r=>Number(r.reviewee_id)===CURRENT_USER_ID).sort((a,b)=>Number(b.id)-Number(a.id));
  $('#viewRoot').innerHTML=`<div class="page-heading"><div><div class="eyebrow">YOUR CAMPUS IDENTITY</div><h1>My profile</h1><p>Show the campus what you know and build trust through completed gigs.</p></div><button class="button button-primary" data-action="edit-profile">✎ Edit profile</button></div>
  <div class="two-col"><section class="panel" style="padding:0;overflow:hidden"><div class="profile-cover"></div><div class="profile-main"><div class="profile-avatar-wrap"><div class="avatar profile-avatar ${avatarClass(u.id)}">${esc(initials(u.name))}</div><span class="status-pill status-open">● MUET student</span></div><h2 class="profile-name">${esc(u.name)}</h2><div class="profile-subtitle">${esc(u.major)} · Semester ${esc(u.semester)}</div><p class="profile-bio">${esc(u.bio||'Add a short bio so other students can get to know you.')}</p><div class="panel-title"><h3>Skills & strengths</h3></div><div class="skill-list">${(u.skills||[]).map(s=>`<span class="skill-tag">${esc(s)}</span>`).join('')||'<span class="small-muted">Add skills to your profile.</span>'}</div><div class="profile-stats"><div class="profile-stat"><strong>${mine.length}</strong><span>Gigs posted</span></div><div class="profile-stat"><strong>${completedCount(CURRENT_USER_ID)}</strong><span>Completed</span></div><div class="profile-stat"><strong>${avgRating(CURRENT_USER_ID)}${avgRating(CURRENT_USER_ID)==='New'?'':' ★'}</strong><span>Average rating</span></div></div></div></section>
  <section class="panel"><div class="panel-title"><h3>Reviews from students</h3><span>${userReviews.length} reviews</span></div>${userReviews.length?userReviews.map(r=>{const author=userById(r.reviewer_id);return `<div class="review-card"><div class="review-head"><div class="avatar ${avatarClass(author?.id)}">${esc(initials(author?.name))}</div><strong>${esc(author?.name||'Student')}</strong><span>★ ${r.rating}.0</span></div><p>${esc(r.comment)}</p></div>`}).join(''):emptyState('Your reputation starts here','Complete a gig and exchange a review to build trust.') }
  <div class="notice" style="margin-top:18px">Tip: a clear bio and specific skills help other students decide whether to work with you.</div></section></div>
  <div class="section-head" style="margin-top:25px"><div><h2>Your recent gigs</h2><p>Your activity in the campus marketplace.</p></div><button class="text-button" data-action="go-my-gigs">View all ↗</button></div><div class="gig-grid">${mine.slice(-3).reverse().map(gigCard).join('')||emptyState('No activity yet','Post your first gig to get started.')}</div>`;
}
function openModal(title,subtitle,body){
  $('#modalRoot').innerHTML=`<div class="modal-backdrop" data-action="backdrop-close"><section class="modal" role="dialog" aria-modal="true" aria-label="${esc(title)}"><header class="modal-header"><div><h2>${esc(title)}</h2><p>${esc(subtitle||'')}</p></div><button class="modal-close" data-action="close-modal" aria-label="Close">×</button></header><div class="modal-body">${body}</div></section></div>`;
  const first=$('input,textarea,select,button', $('#modalRoot'));if(first)first.focus();
}
function closeModal(){ $('#modalRoot').innerHTML=''; }
function openPostModal(){
  openModal('Post a new gig','Tell your campus community what you can offer or what kind of help you need.',`
  <form id="postForm"><div class="form-grid">
    <div class="form-field full"><label>I'm creating a…</label><div class="type-options"><button type="button" class="type-option selected" data-type-choice="Offering"><strong>✦ Offering a skill</strong><span>I can help someone with this.</span></button><button type="button" class="type-option" data-type-choice="Requesting"><strong>⌕ Requesting help</strong><span>I need someone to help me.</span></button></div><input type="hidden" name="type" value="Offering"></div>
    <div class="form-field full"><label for="gigTitle">Gig title *</label><input id="gigTitle" name="title" required maxlength="90" placeholder="e.g. I can design your project presentation"></div>
    <div class="form-field full"><label for="gigDescription">Description *</label><textarea id="gigDescription" name="description" required maxlength="800" placeholder="Describe the task, what you need, and what a successful result looks like…"></textarea></div>
    <div class="form-field"><label for="gigCategory">Category *</label><select id="gigCategory" name="category" required>${CATEGORIES.slice(1).map(c=>`<option>${c}</option>`).join('')}</select></div>
    <div class="form-field"><label for="gigPayment">Payment type *</label><select id="gigPayment" name="payment_type"><option value="Paid">Paid</option><option value="SkillSwap">Skill swap</option><option value="Free">Free</option></select></div>
    <div class="form-field" id="budgetField"><label for="gigBudget">Budget (PKR) *</label><input id="gigBudget" name="budget" type="number" min="1" placeholder="e.g. 1500"></div>
    <div class="form-field"><label for="gigDeadline">Deadline *</label><input id="gigDeadline" name="deadline" type="date" min="${new Date().toISOString().slice(0,10)}" value="${new Date(Date.now()+7*86400000).toISOString().slice(0,10)}" required></div>
  </div><div class="form-footer"><button type="button" class="button button-secondary" data-action="close-modal">Cancel</button><button type="submit" class="button button-primary">Publish gig ↗</button></div></form>`);
  $$('[data-type-choice]').forEach(btn=>btn.addEventListener('click',()=>{
    $$('[data-type-choice]').forEach(b=>b.classList.toggle('selected',b===btn));
    $('input[name="type"]',$('#postForm')).value=btn.dataset.typeChoice;
  }));
  $('#gigPayment').addEventListener('change',e=>{$('#budgetField').style.display=e.target.value==='Paid'?'grid':'none';$('#gigBudget').required=e.target.value==='Paid';});
  $('#postForm').addEventListener('submit',submitGig);
}
async function submitGig(e){
  e.preventDefault();const f=new FormData(e.currentTarget);
  const pay=f.get('payment_type'),budget=pay==='Paid'?Number(f.get('budget')):null;
  const data={user_id:CURRENT_USER_ID,title:String(f.get('title')).trim(),description:String(f.get('description')).trim(),type:f.get('type'),category:f.get('category'),payment_type:pay,budget,deadline:f.get('deadline'),status:'Open',accepted_applicant_id:null,created_at:new Date().toISOString()};
  if(!data.title||!data.description){toast('Please fill in the title and description.','error');return;}
  if(pay==='Paid'&&(!budget||budget<1)){toast('Enter a valid budget for a paid gig.','error');return;}
  try{await api('/gigs',{method:'POST',body:JSON.stringify(data)});await refreshData();closeModal();navTo('my-gigs');toast('Your gig is live on the campus marketplace!','success');}
  catch(err){toast(`Couldn't publish gig: ${err.message}. Is the API running?`,'error');}
}
function openApplyModal(gigId){
  const g=gigById(gigId);if(!g)return;
  if(Number(g.user_id)===CURRENT_USER_ID){toast('You cannot apply to your own gig.','error');return;}
  const existing=state.applications.find(a=>Number(a.gig_id)===Number(g.id)&&Number(a.applicant_id)===CURRENT_USER_ID);
  if(existing){toast(`You already applied. Status: ${existing.status}.`);return;}
  if(!canApply(g)){toast('This gig is no longer open for applications.','error');return;}
  openModal('Apply to this gig',g.title,`<div class="notice">Keep your message short and specific. Tell the gig owner why you're a good fit.</div><form id="applyForm"><div class="form-field"><label for="applyMessage">Message to the gig owner *</label><textarea id="applyMessage" name="message" required maxlength="500" placeholder="Hi! I can help with this because…"></textarea></div><div class="form-footer"><button type="button" class="button button-secondary" data-action="close-modal">Cancel</button><button type="submit" class="button button-primary">Send application ↗</button></div></form>`);
  $('#applyForm').addEventListener('submit',async e=>{e.preventDefault();const message=new FormData(e.currentTarget).get('message').trim();if(!message)return;
    try{await api('/applications',{method:'POST',body:JSON.stringify({gig_id:g.id,applicant_id:CURRENT_USER_ID,message,status:'Pending',created_at:new Date().toISOString()})});await refreshData();closeModal();render();toast('Application sent! Good luck.','success');}
    catch(err){toast(`Couldn't apply: ${err.message}`,'error');}
  });
}
function openDetails(gigId){
  const g=gigById(gigId);if(!g)return;const owner=userById(g.user_id)||{};const status=displayStatus(g);
  const apps=state.applications.filter(a=>Number(a.gig_id)===Number(g.id));
  const own=Number(g.user_id)===CURRENT_USER_ID;
  const myApp=apps.find(a=>Number(a.applicant_id)===CURRENT_USER_ID);
  const price=g.payment_type==='Paid'?money(g.budget):g.payment_type==='Free'?'Free / volunteer':'Skill exchange';
  let actions=own&&status==='Open'?`<button class="button button-primary" data-action="manage-gig" data-id="${g.id}">Manage applicants</button>`:canApply(g)&&!myApp?`<button class="button button-primary" data-action="apply" data-id="${g.id}">Apply to this gig ↗</button>`:myApp?`<span class="status-pill ${statusClass(myApp.status)}">Your application: ${esc(myApp.status)}</span>`:'';
  openModal('Gig details',`${g.category} · Posted by ${owner.name||'Student'}`,`<div class="detail-block"><div class="gig-top"><span class="category-label">${esc(g.type)}</span><span class="status-pill ${statusClass(status)}">${esc(status)}</span></div><h2 class="detail-title">${esc(g.title)}</h2><p class="detail-description">${esc(g.description)}</p><div class="detail-meta"><span>◉ ${esc(g.category)}</span><span>◷ Deadline: ${esc(g.deadline||'Flexible')}</span><span>◈ ${esc(price)}</span></div><div class="gig-owner" style="border:0;padding-top:0;margin-top:18px"><div class="avatar ${avatarClass(owner.id)}">${esc(initials(owner.name))}</div><div class="owner-info"><strong>${esc(owner.name||'Student')}</strong><span>${esc(owner.major||'MUET student')} · ★ ${avgRating(owner.id)}</span></div><span class="small-muted">${apps.length} application${apps.length===1?'':'s'}</span></div></div><div class="detail-section"><h3>About this gig</h3><p class="detail-description">This is a ${esc(g.type.toLowerCase())} gig in ${esc(g.category)}. Payment arrangement: ${esc(paymentText(g.payment_type))}. Please communicate clearly and agree on the expected deliverables before beginning.</p><div class="form-footer" style="justify-content:flex-start">${actions}<button class="button button-secondary" data-action="close-modal">Close</button></div></div>`);
}
function openManageGig(gigId){
  const g=gigById(gigId);if(!g)return;if(Number(g.user_id)!==CURRENT_USER_ID){toast('Only the gig owner can manage applicants.','error');return;}
  const apps=state.applications.filter(a=>Number(a.gig_id)===Number(g.id));
  const rows=apps.map(a=>{const applicant=userById(a.applicant_id)||{};return `<div class="list-row"><div class="avatar ${avatarClass(applicant.id)}">${esc(initials(applicant.name))}</div><div class="row-info"><strong>${esc(applicant.name||'Student')} <span class="small-muted">· ${esc(applicant.major||'')}</span></strong><span>${esc(a.message)}</span></div><span class="status-pill ${statusClass(a.status)}">${esc(a.status)}</span><div class="row-actions">${a.status==='Pending'&&displayStatus(g)==='Open'?`<button class="mini-btn primary" data-action="accept-app" data-id="${a.id}">Accept</button><button class="mini-btn" data-action="reject-app" data-id="${a.id}">Reject</button>`:''}</div></div>`}).join('');
  const footer=displayStatus(g)==='In Progress'?`<button class="button button-primary" data-action="complete-gig" data-id="${g.id}">✓ Mark gig completed</button>`:'';
  openModal('Manage applicants',g.title,`<div class="notice">Accepting one applicant moves the gig to In Progress and automatically rejects the other pending applications.</div><div class="stack-list">${rows||emptyState('No applications yet','Students who apply will appear here.')}</div><div class="form-footer">${footer}<button class="button button-secondary" data-action="close-modal">Close</button></div>`);
}
async function changeApplication(appId, nextStatus){
  const app=state.applications.find(a=>Number(a.id)===Number(appId));if(!app)return;
  const gig=gigById(app.gig_id);
  if(!gig||Number(gig.user_id)!==CURRENT_USER_ID){toast('Only the gig owner can change application status.','error');return;}
  if(app.status!=='Pending'||displayStatus(gig)!=='Open'){toast('This application is no longer pending.','error');return;}
  try{
    if(nextStatus==='Accepted'){
      await api(`/applications/${app.id}`,{method:'PATCH',body:JSON.stringify({status:'Accepted'})});
      const others=state.applications.filter(a=>Number(a.gig_id)===Number(gig.id)&&Number(a.id)!==Number(app.id)&&a.status==='Pending');
      await Promise.all(others.map(a=>api(`/applications/${a.id}`,{method:'PATCH',body:JSON.stringify({status:'Rejected'})})));
      await api(`/gigs/${gig.id}`,{method:'PATCH',body:JSON.stringify({status:'In Progress',accepted_applicant_id:Number(app.applicant_id)})});
      toast('Applicant accepted. The other pending applications were rejected.','success');
    }else{
      await api(`/applications/${app.id}`,{method:'PATCH',body:JSON.stringify({status:'Rejected'})});toast('Application rejected.');
    }
    await refreshData();if($('#modalRoot').innerHTML.trim())openManageGig(gig.id);else render();
  }catch(err){toast(`Couldn't update application: ${err.message}`,'error');}
}
async function completeGig(gigId){
  const g=gigById(gigId);if(!g)return;
  if(Number(g.user_id)!==CURRENT_USER_ID){toast('Only the owner can mark this gig completed.','error');return;}
  if(g.status!=='In Progress'){toast('Only in-progress gigs can be completed.','error');return;}
  try{await api(`/gigs/${g.id}`,{method:'PATCH',body:JSON.stringify({status:'Completed'})});await refreshData();closeModal();render();toast('Gig marked completed! You can now exchange reviews.','success');}
  catch(err){toast(`Couldn't complete gig: ${err.message}`,'error');}
}
function openReviewModal(gigId){
  const g=gigById(gigId);if(!g||g.status!=='Completed'){toast('Reviews are available after a gig is completed.','error');return;}
  const applicantId=Number(g.accepted_applicant_id);
  const revieweeId=Number(g.user_id)===CURRENT_USER_ID?applicantId:Number(g.user_id);
  if(!revieweeId||(![Number(g.user_id),applicantId].includes(CURRENT_USER_ID))){toast('Only the gig owner and accepted applicant can review each other.','error');return;}
  const already=state.reviews.find(r=>Number(r.gig_id)===Number(g.id)&&Number(r.reviewer_id)===CURRENT_USER_ID);
  if(already){toast('You have already reviewed this gig.');return;}
  const person=userById(revieweeId);
  state.selectedRating=5;
  openModal('Leave a review',`Share your experience working with ${person?.name||'this student'}.`,`<form id="reviewForm"><div class="form-field"><label>Rating *</label><div class="rating-picker">${[1,2,3,4,5].map(n=>`<button type="button" class="rating-star ${n<=5?'selected':''}" data-rating="${n}" aria-label="${n} stars">★</button>`).join('')}</div><span id="ratingText" class="form-help">5 out of 5 — Excellent</span></div><div class="form-field" style="margin-top:16px"><label for="reviewComment">Comment *</label><textarea id="reviewComment" name="comment" required maxlength="500" placeholder="What was it like working together?"></textarea></div><div class="form-footer"><button type="button" class="button button-secondary" data-action="close-modal">Cancel</button><button type="submit" class="button button-primary">Submit review</button></div></form>`);
  const labels={1:'Needs improvement',2:'Fair',3:'Good',4:'Very good',5:'Excellent'};
  $$('[data-rating]').forEach(btn=>btn.addEventListener('click',()=>{state.selectedRating=Number(btn.dataset.rating);$$('[data-rating]').forEach(b=>b.classList.toggle('selected',Number(b.dataset.rating)<=state.selectedRating));$('#ratingText').textContent=`${state.selectedRating} out of 5 — ${labels[state.selectedRating]}`;}));
  $('#reviewForm').addEventListener('submit',async e=>{e.preventDefault();const comment=new FormData(e.currentTarget).get('comment').trim();if(!comment)return;
    try{await api('/reviews',{method:'POST',body:JSON.stringify({gig_id:Number(g.id),reviewer_id:CURRENT_USER_ID,reviewee_id:revieweeId,rating:state.selectedRating,comment,created_at:new Date().toISOString()})});await refreshData();closeModal();render();toast('Review published. Thanks for building trust on campus!','success');}
    catch(err){toast(`Couldn't submit review: ${err.message}`,'error');}
  });
}
function openEditProfile(){
  const u=state.currentUser;
  openModal('Edit your profile','Help other students understand your skills and interests.',`<form id="profileForm"><div class="form-grid"><div class="form-field full"><label for="profileName">Full name *</label><input id="profileName" name="name" required maxlength="80" value="${esc(u.name)}"></div><div class="form-field"><label for="profileMajor">Major / department *</label><input id="profileMajor" name="major" required value="${esc(u.major)}"></div><div class="form-field"><label for="profileSemester">Semester *</label><select id="profileSemester" name="semester">${Array.from({length:8},(_,i)=>i+1).map(n=>`<option value="${n}" ${Number(u.semester)===n?'selected':''}>Semester ${n}</option>`).join('')}</select></div><div class="form-field full"><label for="profileBio">Short bio</label><textarea id="profileBio" name="bio" maxlength="500">${esc(u.bio||'')}</textarea></div><div class="form-field full"><label for="profileSkills">Skills (comma-separated)</label><input id="profileSkills" name="skills" value="${esc((u.skills||[]).join(', '))}" placeholder="Java, UI design, writing"></div></div><div class="form-footer"><button type="button" class="button button-secondary" data-action="close-modal">Cancel</button><button type="submit" class="button button-primary">Save profile</button></div></form>`);
  $('#profileForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const data={name:f.get('name').trim(),major:f.get('major').trim(),semester:Number(f.get('semester')),bio:f.get('bio').trim(),skills:f.get('skills').split(',').map(s=>s.trim()).filter(Boolean)};if(!data.name||!data.major){toast('Name and major are required.','error');return;}
    try{await api(`/users/${CURRENT_USER_ID}`,{method:'PATCH',body:JSON.stringify(data)});await refreshData();closeModal();render();toast('Profile updated!','success');}
    catch(err){toast(`Couldn't save profile: ${err.message}`,'error');}
  });
}
function showHowItWorks(){
  openModal('How CampusLoop works','A small, trusted marketplace for the campus community.',`<div class="stack-list"><div class="list-row"><div class="stat-icon purple">1</div><div class="row-info"><strong>Post or discover</strong><span>Offer a skill or request help in Programming, Design, Writing, or Tutoring.</span></div></div><div class="list-row"><div class="stat-icon green">2</div><div class="row-info"><strong>Agree on the exchange</strong><span>Choose paid work, a skill swap, or a free collaboration. Apply with a clear message.</span></div></div><div class="list-row"><div class="stat-icon amber">3</div><div class="row-info"><strong>Work together</strong><span>The gig owner accepts one applicant, and the gig moves to In Progress.</span></div></div><div class="list-row"><div class="stat-icon blue">4</div><div class="row-info"><strong>Complete and review</strong><span>After completion, both participants can review each other and build reputation.</span></div></div></div><div class="form-footer"><button class="button button-primary" data-action="close-modal">Got it</button></div>`);
}
document.addEventListener('click',async e=>{
  const nav=e.target.closest('[data-view]');if(nav){navTo(nav.dataset.view);return;}
  const btn=e.target.closest('[data-action]');if(!btn)return;
  const action=btn.dataset.action,id=btn.dataset.id;
  if(action==='post')openPostModal();
  else if(action==='close-modal')closeModal();
  else if(action==='details')openDetails(id);
  else if(action==='apply')openApplyModal(id);
  else if(action==='manage-gig')openManageGig(id);
  else if(action==='accept-app')await changeApplication(id,'Accepted');
  else if(action==='reject-app')await changeApplication(id,'Rejected');
  else if(action==='complete-gig')await completeGig(id);
  else if(action==='edit-profile')openEditProfile();
  else if(action==='status-filter'){state.status=btn.dataset.status;renderDiscover();}
  else if(action==='reset-filters'){state.search='';state.category='All categories';state.type='All types';state.payment='All payment types';state.status='All statuses';state.minBudget='';state.maxBudget='';renderDiscover();}
  else if(action==='how')showHowItWorks();
  else if(action==='go-my-gigs')navTo('my-gigs');
  else if(action==='edit-profile-quick')openEditProfile();
  else if(action==='application-status')navTo('applications');
  else if(action==='backdrop-close'&&e.target===btn)closeModal();
  else if(action==='review')openReviewModal(id);
});
$('#topPostBtn').addEventListener('click',openPostModal);
$('#helpPostBtn').addEventListener('click',openPostModal);
$('#editProfileQuick').addEventListener('click',openEditProfile);
$('#demoUserSwitch')?.addEventListener('change',async e=>{const nextId=Number(e.target.value);if(!userById(nextId))return;CURRENT_USER_ID=nextId;state.currentUser=userById(nextId);updateSidebar();render();toast(`Demo account switched to ${state.currentUser.name}.`, 'success');});
async function init(){
  try{await refreshData();render();}
  catch(err){$('#viewRoot').innerHTML=`<div class="empty-state"><div class="empty-icon">⌁</div><h3>Let's connect the mock API</h3><p>CampusLoop needs the JSON Server API running on port 3000. Open a second terminal and run <code>npm run api</code>, then refresh this page.</p><button class="button button-primary" data-action="retry">Try again</button></div>`;toast('API connection failed. Start JSON Server in a second terminal.','error');}
}
document.addEventListener('click',async e=>{const b=e.target.closest('[data-action="retry"]');if(b){try{await refreshData();render();toast('Connected to the API.','success')}catch{toast('Still unable to connect. Check that npm run api is running.','error')}}});
init();
