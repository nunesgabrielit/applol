const ROLE_KEYS = ["top", "jungler", "mid", "carry", "sup"];

const state = {
  champions: [],
  filteredChampions: [],
  selectedChampion: null,
  meta: null,
  tags: [],
  guideItems: [],
  search: "",
  tag: "",
  sortBy: "name",
  order: "asc",
  recommendation: null,
  guideChampionNames: [],
  selectedChampionPerformance: null,
  selectedChampionDataset: null,
  searchSuggestions: [],
  selectedChampionProfileIndex: 0,
};

const els = {
  healthStatus: document.querySelector("#healthStatus"),
  versionBadge: document.querySelector("#versionBadge"),
  localeBadge: document.querySelector("#localeBadge"),
  guideCountBadge: document.querySelector("#guideCountBadge"),
  refreshButton: document.querySelector("#refreshButton"),
  searchInput: document.querySelector("#searchInput"),
  searchbox: document.querySelector("#searchbox"),
  searchSuggestions: document.querySelector("#searchSuggestions"),
  tagSelect: document.querySelector("#tagSelect"),
  sortBySelect: document.querySelector("#sortBySelect"),
  orderSelect: document.querySelector("#orderSelect"),
  enemyTop: document.querySelector("#enemyTop"),
  enemyJungler: document.querySelector("#enemyJungler"),
  enemyMid: document.querySelector("#enemyMid"),
  enemyCarry: document.querySelector("#enemyCarry"),
  enemySup: document.querySelector("#enemySup"),
  analyzeButton: document.querySelector("#analyzeButton"),
  clearDraftButton: document.querySelector("#clearDraftButton"),
  copyDraftButton: document.querySelector("#copyDraftButton"),
  shareDraftButton: document.querySelector("#shareDraftButton"),
  suggestedAdc: document.querySelector("#suggestedAdc"),
  suggestedAdcHint: document.querySelector("#suggestedAdcHint"),
  suggestedSupport: document.querySelector("#suggestedSupport"),
  suggestedSupportHint: document.querySelector("#suggestedSupportHint"),
  adcSuggestionCard: document.querySelector("#adcSuggestionCard"),
  supportSuggestionCard: document.querySelector("#supportSuggestionCard"),
  adcRanking: document.querySelector("#adcRanking"),
  supportRanking: document.querySelector("#supportRanking"),
  recommendationStatus: document.querySelector("#recommendationStatus"),
  recommendationWarnings: document.querySelector("#recommendationWarnings"),
  shareDraftSummary: document.querySelector("#shareDraftSummary"),
  matchedSummary: document.querySelector("#matchedSummary"),
  matchedCounters: document.querySelector("#matchedCounters"),
  championsGrid: document.querySelector("#championsGrid"),
  detailPanel: document.querySelector("#detailPanel"),
  resultsSummary: document.querySelector("#resultsSummary"),
  featuredChampion: document.querySelector("#featuredChampion"),
  featuredDescription: document.querySelector("#featuredDescription"),
  tagCloud: document.querySelector("#tagCloud"),
  championCardTemplate: document.querySelector("#championCardTemplate"),
  comboboxes: Array.from(document.querySelectorAll(".combobox")),
  catalogPanel: document.querySelector("#roster-panel"),
  explorerPanel: document.querySelector("#explorer-panel"),
  analyticsSummary: document.querySelector("#analyticsSummary"),
  analyticsDeck: document.querySelector("#champion-deck"),
  analyticsFocus: document.querySelector("#analyticsFocus"),
  mostPresentList: document.querySelector("#mostPresentList"),
  enemyAppearanceList: document.querySelector("#enemyAppearanceList"),
  analyticsAdcList: document.querySelector("#analyticsAdcList"),
  analyticsSupportList: document.querySelector("#analyticsSupportList"),
  heroNavLinks: Array.from(document.querySelectorAll(".hero__nav-link")),
  backToTopButton: document.querySelector("#backToTopButton"),
};

init().catch((error) => {
  showToast(error.message || "Nao foi possivel carregar a interface.", true);
});

async function init() {
  bindEvents();
  await Promise.all([
    loadHealth(),
    loadMeta(),
    loadTags(),
    loadGuide(),
    loadChampions(),
  ]);
  render();
  initRevealAnimations();
}

function bindEvents() {
  els.searchInput.addEventListener("input", (event) => {
    state.search = event.target.value.trim();
    applyFilters();
    renderChampions();
    renderSearchSuggestions();
  });

  els.searchInput.addEventListener("focus", () => {
    renderSearchSuggestions();
    openSearchSuggestions();
  });

  els.searchInput.addEventListener("keydown", handleSearchKeydown);

  els.tagSelect.addEventListener("change", (event) => {
    state.tag = event.target.value;
    applyFilters();
    renderChampions();
    renderTagCloud();
  });

  els.sortBySelect.addEventListener("change", (event) => {
    state.sortBy = event.target.value;
    applyFilters();
    renderChampions();
  });

  els.orderSelect.addEventListener("change", (event) => {
    state.order = event.target.value;
    applyFilters();
    renderChampions();
  });

  els.analyzeButton.addEventListener("click", analyzeDraft);

  els.clearDraftButton.addEventListener("click", () => {
    ROLE_KEYS.forEach((role) => {
      getRoleInput(role).value = "";
    });
    closeAllComboboxes();
    renderGuideOptions();
    state.recommendation = null;
    renderRecommendation();
  });

  els.copyDraftButton.addEventListener("click", copyDraftSummary);
  els.shareDraftButton.addEventListener("click", shareDraftSummary);

  if (els.refreshButton) {
    els.refreshButton.addEventListener("click", async () => {
      els.refreshButton.disabled = true;
      els.refreshButton.textContent = "Atualizando...";
      try {
        await request("/refresh", { method: "POST" });
        await Promise.all([loadMeta(), loadTags(), loadChampions()]);
        showToast("Cache da API atualizado com sucesso.");
      } catch (error) {
        showToast(error.message || "Falha ao atualizar o cache.", true);
      } finally {
        els.refreshButton.disabled = false;
        els.refreshButton.textContent = "Atualizar cache";
      }
    });
  }

  bindComboboxEvents();
  document.addEventListener("click", handleDocumentClick);
  document.addEventListener("keydown", handleGlobalKeydown);
  window.addEventListener("scroll", handleWindowScroll, { passive: true });
  els.backToTopButton?.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  updateSectionNavigation();
}

function initRevealAnimations() {
  const targets = Array.from(
    document.querySelectorAll(
      ".panel, .detail, .analytics-panel, .hero__nav--floating, .share-strip, .recommendation-card"
    )
  );

  if (!targets.length) {
    return;
  }

  const prefersReducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
  if (prefersReducedMotion || !("IntersectionObserver" in window)) {
    targets.forEach((target) => target.classList.add("is-visible"));
    return;
  }

  targets.forEach((target, index) => {
    target.classList.add("reveal-on-scroll");
    target.style.setProperty("--reveal-delay", `${Math.min(index * 55, 240)}ms`);
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }

        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    {
      rootMargin: "0px 0px -8% 0px",
      threshold: 0.14,
    }
  );

  targets.forEach((target) => observer.observe(target));
}

async function loadHealth() {
  const payload = await request("/health");
  els.healthStatus.textContent = payload.status === "ok" ? "Online" : "Instavel";
}

async function loadMeta() {
  state.meta = await request("/meta");
  els.versionBadge.textContent = state.meta.ddragon_version;
  els.localeBadge.textContent = state.meta.language;
}

async function loadTags() {
  const payload = await request("/tags");
  state.tags = payload.items;
  renderTagOptions();
  renderTagCloud();
}

async function loadGuide() {
  const payload = await request("/counters");
  state.guideItems = payload.items;
  els.guideCountBadge.textContent = String(payload.total);
  renderGuideOptions();
}

async function loadChampions() {
  const payload = await request("/champions?limit=300&sort_by=name&order=asc");
  state.champions = payload.items;
  state.searchSuggestions = payload.items;
  if (!state.selectedChampion && payload.items.length) {
    await selectChampion(payload.items[0].key);
  }
  applyFilters();
}

async function analyzeDraft() {
  const payload = {
    top: els.enemyTop.value.trim() || null,
    jungler: els.enemyJungler.value.trim() || null,
    mid: els.enemyMid.value.trim() || null,
    carry: els.enemyCarry.value.trim() || null,
    sup: els.enemySup.value.trim() || null,
  };

  state.recommendation = await request("/counters/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  renderRecommendation();
}

function render() {
  renderTagCloud();
  renderMetaSpotlight();
  renderRecommendation();
  renderChampionDeck();
  renderChampions();
}

function renderGuideOptions() {
  state.guideChampionNames = state.guideItems
    .map((item) => item.enemy_champion)
    .filter((value, index, items) => items.indexOf(value) === index)
    .sort((left, right) => left.localeCompare(right, "pt-BR"));

  els.comboboxes.forEach((combobox) => {
    renderComboboxOptions(combobox);
  });
}

function renderRecommendation() {
  const data = state.recommendation;
  if (!data) {
    els.suggestedAdc.textContent = "-";
    els.suggestedAdcHint.textContent = "Preencha Top, Jungler, Mid, Carry e Sup para calcular.";
    els.suggestedSupport.textContent = "-";
    els.suggestedSupportHint.textContent = "A votacao da sua planilha aparecera aqui.";
    els.adcRanking.innerHTML = '<div class="empty-state">Sem ranking ainda.</div>';
    els.supportRanking.innerHTML = '<div class="empty-state">Sem ranking ainda.</div>';
    els.matchedCounters.innerHTML = '<div class="empty-state">Os counters reconhecidos por lane aparecerao aqui.</div>';
    els.matchedSummary.textContent = "Os counters reconhecidos vao aparecer aqui.";
    els.recommendationStatus.textContent = "Nenhuma analise executada ainda.";
    els.recommendationWarnings.hidden = true;
    els.recommendationWarnings.innerHTML = "";
    els.shareDraftSummary.textContent = "O resumo do draft ficara pronto aqui para copiar ou compartilhar.";
    applySuggestionArt(els.adcSuggestionCard, null);
    applySuggestionArt(els.supportSuggestionCard, null);
    return;
  }

  els.suggestedAdc.textContent = data.suggested_adc ? data.suggested_adc.champion : "-";
  els.suggestedAdcHint.textContent = data.suggested_adc
    ? `${data.suggested_adc.votes} voto(s) no seu guia.`
    : "Nenhum ADC sugerido com os dados atuais.";

  els.suggestedSupport.textContent = data.suggested_support ? data.suggested_support.champion : "-";
  els.suggestedSupportHint.textContent = data.suggested_support
    ? `${data.suggested_support.votes} voto(s) no seu guia.`
    : "Nenhum suporte sugerido com os dados atuais.";

  applySuggestionArt(
    els.adcSuggestionCard,
    data.suggested_adc ? getChampionSplashUrl(data.suggested_adc.champion) : null,
  );
  applySuggestionArt(
    els.supportSuggestionCard,
    data.suggested_support ? getChampionSplashUrl(data.suggested_support.champion) : null,
  );

  renderRanking(els.adcRanking, data.adc_ranking, "Nenhum ranking de ADC gerado.");
  renderRanking(els.supportRanking, data.support_ranking, "Nenhum ranking de suporte gerado.");
  renderMatchedCounters(data.matched_counters);
  animateRecommendationBlocks();

  els.matchedSummary.textContent = `${data.matched_counters.length} lane(s) reconhecida(s) na sua planilha.`;

  const warnings = [];
  if (data.missing_roles.length) {
    warnings.push(`Campos vazios: ${data.missing_roles.join(", ")}`);
  }
  if (data.unknown_entries.length) {
    warnings.push(`Nao encontrados na base: ${data.unknown_entries.join(" | ")}`);
  }

  els.recommendationStatus.textContent = warnings.length
    ? "Analise concluida com observacoes."
    : "Analise concluida com sucesso.";

  if (warnings.length) {
    els.recommendationWarnings.hidden = false;
    els.recommendationWarnings.innerHTML = warnings.map((item) => `<div>${item}</div>`).join("");
  } else {
    els.recommendationWarnings.hidden = true;
    els.recommendationWarnings.innerHTML = "";
  }

  els.shareDraftSummary.textContent = buildRecommendationShareText(data);
}

function renderRanking(root, items, emptyText) {
  root.innerHTML = "";
  if (!items.length) {
    root.innerHTML = `<div class="empty-state">${emptyText}</div>`;
    return;
  }

  items.slice(0, 5).forEach((item, index) => {
    const row = document.createElement("div");
    row.className = `ranking-item${index === 0 ? " ranking-item--top" : ""}`;
    const avatarUrl = getChampionIconUrl(item.champion);
    row.innerHTML = `
      <div class="ranking-item__left">
        ${avatarUrl ? `<img class="ranking-item__avatar" src="${avatarUrl}" alt="${item.champion}" />` : ""}
        <span class="ranking-item__name">${index + 1}. ${item.champion}</span>
      </div>
      <strong>${item.votes} voto(s)</strong>
    `;
    root.appendChild(row);
  });
}

function animateRecommendationBlocks() {
  [
    els.adcSuggestionCard,
    els.supportSuggestionCard,
    els.adcRanking.closest(".panel"),
    els.supportRanking.closest(".panel"),
    els.matchedCounters,
  ]
    .filter(Boolean)
    .forEach((node, index) => {
      node.classList.remove("cinematic-enter", "cinematic-enter-delay-1", "cinematic-enter-delay-2", "cinematic-enter-delay-3");
      void node.offsetWidth;
      node.classList.add("cinematic-enter");
      if (index === 1) node.classList.add("cinematic-enter-delay-1");
      if (index === 2) node.classList.add("cinematic-enter-delay-2");
      if (index >= 3) node.classList.add("cinematic-enter-delay-3");
    });
}

function renderMatchedCounters(items) {
  els.matchedCounters.innerHTML = "";
  if (!items.length) {
    els.matchedCounters.innerHTML = '<div class="empty-state">Nenhum inimigo reconhecido na base ainda.</div>';
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "match-card";
    const splashUrl = getChampionSplashUrl(item.enemy_champion);
    const iconUrl = getChampionIconUrl(item.enemy_champion);
    if (splashUrl) {
      card.style.setProperty("--enemy-splash", `url("${splashUrl}")`);
    }
    card.innerHTML = `
      <div class="match-card__header">
        <div class="match-card__identity">
          ${iconUrl ? `<img class="match-card__avatar" src="${iconUrl}" alt="${item.enemy_champion}" />` : ""}
          <div>
            <div class="panel__eyebrow">${item.role}</div>
            <div class="match-card__enemy">${item.enemy_champion}</div>
          </div>
        </div>
        <div class="match-card__choices">
          <span class="tag-badge">ADC: ${item.ideal_adc}</span>
          <span class="tag-badge">Sup: ${item.ideal_support}</span>
        </div>
      </div>
      <p class="match-card__reason">${item.reason}</p>
    `;
    els.matchedCounters.appendChild(card);
  });
}

function applyFilters() {
  const search = normalizeText(state.search);
  const tag = normalizeText(state.tag);

  state.filteredChampions = state.champions
    .filter((champion) => {
      const matchesSearch =
        !search ||
        normalizeText(champion.name).includes(search) ||
        normalizeText(champion.riot_id).includes(search) ||
        normalizeText(String(champion.key)).includes(search);

      const matchesTag =
        !tag || champion.tags.some((championTag) => normalizeText(championTag) === tag);

      return matchesSearch && matchesTag;
    })
    .sort((left, right) => {
      const prioritized = compareTagPriority(left, right, tag);
      if (prioritized !== 0) {
        return prioritized;
      }
      if (search) {
        const searchPriority = compareSearchPriority(left, right, search);
        if (searchPriority !== 0) {
          return searchPriority;
        }
      }
      return sortChampions(left, right, state.sortBy, state.order);
    });
}

function sortChampions(left, right, sortBy, order) {
  const direction = order === "desc" ? -1 : 1;
  if (sortBy === "key") {
    return (Number(left.key) - Number(right.key)) * direction;
  }
  return left.name.localeCompare(right.name, "pt-BR") * direction;
}

function renderChampions() {
  els.championsGrid.innerHTML = "";
  if (!state.filteredChampions.length) {
    els.resultsSummary.textContent = "Nenhum campeao encontrado para os filtros atuais.";
    els.championsGrid.innerHTML = '<div class="empty-state">Tente outro nome, role ou ordenacao.</div>';
    return;
  }

  els.resultsSummary.textContent = `${state.filteredChampions.length} campeoes exibidos`;
  state.filteredChampions.forEach((champion) => {
    const node = els.championCardTemplate.content.firstElementChild.cloneNode(true);
    node.querySelector(".champion-card__art").style.backgroundImage = `url("${champion.icon_url}")`;
    node.querySelector(".champion-card__name").textContent = champion.name;
    node.querySelector(".champion-card__key").textContent = `#${champion.key}`;
    node.querySelector(".champion-card__title").textContent = champion.title;
    const tagsRoot = node.querySelector(".champion-card__tags");
    champion.tags.forEach((tag) => {
      const badge = document.createElement("button");
      badge.type = "button";
      badge.className = `tag-badge tag-badge--interactive${isTagActive(tag) ? " is-active" : ""}`;
      badge.textContent = tag;
      badge.addEventListener("click", (event) => {
        event.stopPropagation();
        activateTagFilter(tag);
      });
      tagsRoot.appendChild(badge);
    });
    if (state.selectedChampion && Number(state.selectedChampion.key) === Number(champion.key)) {
      node.classList.add("is-active");
    }
    node.addEventListener("click", async () => {
      await selectChampion(champion.key);
      renderChampions();
      if (els.analyticsDeck) {
        els.analyticsDeck.scrollIntoView({ behavior: "smooth", block: "start" });
        els.analyticsDeck.classList.remove("analytics-deck--focus");
        void els.analyticsDeck.offsetWidth;
        els.analyticsDeck.classList.add("analytics-deck--focus");
      }
    });
    els.championsGrid.appendChild(node);
  });
}

function renderTagOptions() {
  els.tagSelect.innerHTML = '<option value="">Todas</option>';
  state.tags.forEach((tag) => {
    const option = document.createElement("option");
    option.value = tag;
    option.textContent = tag;
    els.tagSelect.appendChild(option);
  });
}

function renderSearchSuggestions() {
  if (!els.searchSuggestions) {
    return;
  }

  const search = normalizeText(state.search || els.searchInput.value || "");
  const items = state.searchSuggestions
    .filter((champion) => {
      return (
        !search ||
        normalizeText(champion.name).includes(search) ||
        normalizeText(champion.riot_id).includes(search) ||
        normalizeText(String(champion.key)).includes(search)
      );
    })
    .sort((left, right) => compareSearchPriority(left, right, search) || sortChampions(left, right, "name", "asc"));

  els.searchSuggestions.innerHTML = "";

  if (!items.length) {
    els.searchSuggestions.innerHTML = '<div class="searchbox__empty">Nenhum campeao encontrado.</div>';
    return;
  }

  items.forEach((champion) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "searchbox__option";
    button.innerHTML = `
      <span class="searchbox__option-name">${champion.name}</span>
    `;
    button.addEventListener("click", async () => {
      els.searchInput.value = champion.name;
      state.search = champion.name;
      applyFilters();
      renderChampions();
      closeSearchSuggestions();
      await selectChampion(champion.key);
      renderChampions();
      if (els.analyticsDeck) {
        els.analyticsDeck.scrollIntoView({ behavior: "smooth", block: "start" });
        els.analyticsDeck.classList.remove("analytics-deck--focus");
        void els.analyticsDeck.offsetWidth;
        els.analyticsDeck.classList.add("analytics-deck--focus");
      }
    });
    els.searchSuggestions.appendChild(button);
  });
}

function openSearchSuggestions() {
  if (!els.searchSuggestions) {
    return;
  }
  els.searchSuggestions.hidden = false;
}

function closeSearchSuggestions() {
  if (!els.searchSuggestions) {
    return;
  }
  els.searchSuggestions.hidden = true;
}

async function handleSearchKeydown(event) {
  if (event.key === "Escape") {
    closeSearchSuggestions();
    return;
  }

  if (event.key === "Enter") {
    const firstSuggestion = els.searchSuggestions?.querySelector(".searchbox__option");
    if (firstSuggestion) {
      event.preventDefault();
      firstSuggestion.click();
    }
  }
}

function renderTagCloud() {
  els.tagCloud.innerHTML = "";
  state.tags.slice(0, 8).forEach((tag) => {
    const badge = document.createElement("button");
    badge.type = "button";
    badge.className = `tag-badge tag-badge--interactive${isTagActive(tag) ? " is-active" : ""}`;
    badge.innerHTML = `
      <span>${tag}</span>
      <span class="tag-badge__count">${countChampionsByTag(tag)}</span>
    `;
    badge.title = `Filtrar catalogo por ${tag}`;
    badge.addEventListener("click", () => activateTagFilter(tag));
    els.tagCloud.appendChild(badge);
  });

  if (state.tag) {
    const clearBadge = document.createElement("button");
    clearBadge.type = "button";
    clearBadge.className = "tag-badge tag-badge--clear";
    clearBadge.textContent = "Limpar filtro";
    clearBadge.addEventListener("click", clearTagFilter);
    els.tagCloud.appendChild(clearBadge);
  }
}

function renderMetaSpotlight() {
  if (!state.selectedChampion) {
    els.featuredChampion.textContent = "-";
    els.featuredDescription.textContent = "Selecione um campeao para ver os detalhes.";
    return;
  }
  els.featuredChampion.textContent = state.selectedChampion.name;
  els.featuredDescription.textContent =
    state.selectedChampion.blurb ||
    `${state.selectedChampion.name} atua como ${state.selectedChampion.tags.join(", ")}.`;
}

async function selectChampion(key) {
  const [champion, performance, dataset] = await Promise.all([
    request(`/champions/${key}`),
    request(`/champions/${key}/performance`).catch(() => null),
    request(`/analytics/champions/${key}`).catch(() => null),
  ]);
  state.selectedChampion = champion;
  state.selectedChampionPerformance = performance;
  state.selectedChampionDataset = dataset;
  state.selectedChampionProfileIndex = 0;
  renderMetaSpotlight();
  renderDetail();
  renderChampionDeck();
  bindChampionJumpButtons();
}

function renderDetail() {
  const champion = state.selectedChampion;
  if (!champion) {
    els.detailPanel.innerHTML = '<div class="detail__empty">Nenhum campeao selecionado.</div>';
    return;
  }

  const stats = Object.entries(champion.stats || {}).slice(0, 8);
  els.detailPanel.innerHTML = `
    <div class="detail__overview">
      <div class="detail__hero-card">
        <div class="detail__hero">
          <img class="detail__icon" src="${champion.icon_url}" alt="${champion.name}" />
          <div>
            <div class="panel__eyebrow">Champion focus</div>
            <h3 class="detail__name">${champion.name}</h3>
            <div class="detail__title">${champion.title}</div>
          </div>
        </div>
      </div>
      <div class="detail__stats">
        <article class="detail-stat"><div class="detail-stat__label">Riot ID</div><div class="detail-stat__value">${champion.riot_id}</div></article>
        <article class="detail-stat"><div class="detail-stat__label">Partype</div><div class="detail-stat__value">${champion.partype || "N/A"}</div></article>
        <article class="detail-stat"><div class="detail-stat__label">Roles</div><div class="detail-stat__value">${champion.tags.join(", ") || "N/A"}</div></article>
        <article class="detail-stat"><div class="detail-stat__label">Key</div><div class="detail-stat__value">${champion.key}</div></article>
      </div>
    </div>
    ${renderPerformanceSection(state.selectedChampionPerformance)}
    <div class="detail__blurb">${champion.blurb || "Este campeao nao trouxe blurb no payload atual do Data Dragon."}</div>
    <div class="detail__stats-grid">
      ${stats
        .map(
          ([label, value]) => `
            <article class="summary-stat">
              <div class="summary-stat__label">${label}</div>
              <div class="summary-stat__value">${value}</div>
            </article>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderPerformanceSection(performance) {
  if (!performance) {
    return `
      <section class="performance-card">
        <div class="panel__eyebrow">Meta Snapshot</div>
        <div class="performance-card__summary">Snapshot publico do LoLalytics indisponivel no momento.</div>
      </section>
    `;
  }

  const roleItems = performance.role_stats
    .map((item) => {
      return `
        <div class="performance-chip">
          <strong>${item.label}</strong>
          <span>${formatPercent(item.win_rate)} WR • ${formatPercent(item.pick_rate)} pick</span>
        </div>
      `;
    })
    .join("");

  return `
    <section class="performance-card">
      <div class="panel__eyebrow">LoLalytics</div>
      <div class="performance-card__summary">${performance.summary}</div>
      <div class="performance-card__meta">
        <span class="tag-badge">Tier base: ${performance.tier || "Emerald+"}</span>
        <a class="tag-badge performance-card__link" href="${performance.source_url}" target="_blank" rel="noreferrer">Abrir referencia</a>
      </div>
      <div class="performance-card__roles">
        ${roleItems || '<div class="empty-state">Sem leitura de role disponivel.</div>'}
      </div>
      <div class="performance-matchups">
        ${renderSimpleTagGroup("Counters fortes", performance.strong_against)}
        ${renderSimpleTagGroup("Piores matchups", performance.weak_against)}
      </div>
      <div class="performance-card__note">${performance.caveat}</div>
    </section>
  `;
}

function renderSimpleTagGroup(title, items) {
  const content = items && items.length
    ? items
        .map((item) => {
          const avatarUrl = getChampionIconUrl(item);
          return `
            <button type="button" class="tag-badge tag-badge--interactive performance-tag" data-champion-jump="${item}">
              ${avatarUrl ? `<img class="tag-badge__avatar" src="${avatarUrl}" alt="${item}" />` : ""}
              <span>${item}</span>
            </button>
          `;
        })
        .join("")
    : '<span class="tag-badge">Sem dados</span>';
  return `
    <div class="performance-group">
      <div class="performance-group__label">${title}</div>
      <div class="tag-cloud">${content}</div>
    </div>
  `;
}

function renderChampionDeck() {
  const data = state.selectedChampionDataset;
  if (!data || !state.selectedChampion) {
    els.analyticsSummary.textContent = "Selecione um campeao no Explorer para abrir este painel.";
    els.analyticsFocus.innerHTML = '<div class="empty-state">Counters, against e sinergias do campeao selecionado vao aparecer aqui.</div>';
    renderTagBarList(els.mostPresentList, [], "Sem counters.");
    renderTagBarList(els.enemyAppearanceList, [], "Sem against.");
    renderTagBarList(els.analyticsAdcList, [], "Sem sinergia boa.");
    renderTagBarList(els.analyticsSupportList, [], "Sem sinergia ruim.");
    return;
  }

  els.analyticsSummary.textContent = `${data.name} • ${data.primary_role} • ${data.tags.join(", ")}`;
  const profiles = Array.isArray(data.profiles) && data.profiles.length ? data.profiles : [];
  const activeProfileIndex = Math.max(0, Math.min(state.selectedChampionProfileIndex || 0, profiles.length - 1));
  const profile = profiles[activeProfileIndex];
  els.analyticsFocus.innerHTML = `
    <article class="analytics-focus-card">
      <div class="analytics-focus-card__hero">
        <img class="analytics-focus-card__icon" src="${state.selectedChampion.icon_url}" alt="${data.name}" />
        <div>
          <div class="panel__eyebrow">Selecionado</div>
          <h3 class="analytics-focus-card__title">${data.name}</h3>
          <div class="analytics-focus-card__subtitle">${state.selectedChampion.title}</div>
        </div>
      </div>
      <div class="tag-cloud">
        <span class="tag-badge">Role: ${data.primary_role}</span>
        ${data.tags.map((tag) => `<span class="tag-badge">${tag}</span>`).join("")}
      </div>
      ${profile ? `<div class="analytics-focus-card__active-profile">Perfil ativo: ${profile.label}</div>` : ""}
      ${data.note ? `<div class="analytics-focus-card__note">${data.note}</div>` : ""}
      ${
        profiles.length > 1
          ? `
            <div class="analytics-profile-switcher">
              <div class="analytics-inline-label">Perfis do campeao</div>
              <div class="tag-cloud">
                ${profiles
                  .map(
                    (profileItem, index) => `
                      <button
                        type="button"
                        class="tag-badge tag-badge--interactive analytics-profile-chip${index === activeProfileIndex ? " is-active" : ""}"
                        data-profile-index="${index}"
                      >
                        ${profileItem.label}
                      </button>
                    `,
                  )
                  .join("")}
              </div>
            </div>
          `
          : ""
      }
    </article>
  `;

  els.analyticsFocus.querySelectorAll("[data-profile-index]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedChampionProfileIndex = Number(button.dataset.profileIndex || 0);
      renderChampionDeck();
    });
  });

  if (!profile) {
    renderTagBarList(els.mostPresentList, data.counters, "Sem counters.");
    renderTagBarList(els.enemyAppearanceList, data.against, "Sem against.");
    renderTagBarList(els.analyticsAdcList, data.synergy_good, "Sem sinergia boa.");
    renderTagBarList(els.analyticsSupportList, data.synergy_bad, "Sem sinergia ruim.");
    return;
  }

  renderTagBarList(els.mostPresentList, profile.counters, "Sem counters.");
  renderTagBarList(els.enemyAppearanceList, profile.against, "Sem against.");
  renderSynergyList(els.analyticsAdcList, profile.synergies, profile.synergy_label, "Sem sinergias.");
  renderWarningList(els.analyticsSupportList, profile.warning, data.synergy_bad);
}

function bindChampionJumpButtons() {
  document.querySelectorAll("[data-champion-jump]").forEach((button) => {
    button.addEventListener("click", async () => {
      const championName = button.dataset.championJump || "";
      const champion = state.champions.find(
        (item) =>
          normalizeText(item.name) === normalizeText(championName) ||
          normalizeText(item.riot_id) === normalizeText(championName),
      );

      if (!champion) {
        showToast("Campeao nao encontrado no catalogo local.", true);
        return;
      }

      await selectChampion(champion.key);
      applyFilters();
      renderChampions();

      if (els.analyticsDeck) {
        els.analyticsDeck.scrollIntoView({ behavior: "smooth", block: "start" });
        els.analyticsDeck.classList.remove("analytics-deck--focus");
        void els.analyticsDeck.offsetWidth;
        els.analyticsDeck.classList.add("analytics-deck--focus");
      }
    });
  });
}

function renderBarList(root, items, emptyText) {
  root.innerHTML = "";
  if (!items || !items.length) {
    root.innerHTML = `<div class="empty-state">${emptyText}</div>`;
    return;
  }

  const max = Math.max(...items.map((item) => item.count), 1);
  items.slice(0, 6).forEach((item) => {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div class="bar-row__top">
        <span class="bar-row__label">${item.label}</span>
        <span class="bar-row__value">${item.count} • ${item.share.toFixed(1)}%</span>
      </div>
      <div class="bar-row__track">
        <div class="bar-row__fill" style="width:${(item.count / max) * 100}%"></div>
      </div>
    `;
    root.appendChild(row);
  });
}

function renderTagBarList(root, items, emptyText) {
  root.innerHTML = "";
  if (!items || !items.length) {
    root.innerHTML = `<div class="empty-state">${emptyText}</div>`;
    return;
  }

  items.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "tag-row";
    const avatarUrl = getChampionIconUrl(item);
    row.innerHTML = `
      <span class="tag-row__index">${index + 1}</span>
      ${avatarUrl ? `<img class="tag-row__avatar" src="${avatarUrl}" alt="${item}" />` : ""}
      <span class="tag-row__label">${item}</span>
    `;
    root.appendChild(row);
  });
}

function renderSynergyList(root, synergies, label, emptyText) {
  root.innerHTML = "";
  if (!synergies || !synergies.length) {
    root.innerHTML = `<div class="empty-state">${emptyText}</div>`;
    return;
  }

  const intro = document.createElement("div");
  intro.className = "analytics-inline-label";
  intro.textContent = label;
  root.appendChild(intro);

  synergies.forEach((item) => {
    const row = document.createElement("div");
    row.className = "synergy-row";
    const avatarUrl = getChampionIconUrl(item.champion);
    row.innerHTML = `
      <div class="synergy-row__header">
        ${avatarUrl ? `<img class="synergy-row__avatar" src="${avatarUrl}" alt="${item.champion}" />` : ""}
        <div class="synergy-row__champion">${item.champion}</div>
      </div>
      <div class="synergy-row__reason">${item.reason || "Boa combinacao para o campeao selecionado."}</div>
    `;
    root.appendChild(row);
  });
}

function renderWarningList(root, warning, fallbackItems) {
  root.innerHTML = "";

  if (warning) {
    const warningNode = document.createElement("div");
    warningNode.className = "warning-inline";
    warningNode.textContent = warning;
    root.appendChild(warningNode);
  }

  if (fallbackItems && fallbackItems.length) {
    fallbackItems.forEach((item, index) => {
      const row = document.createElement("div");
      row.className = "tag-row";
      const avatarUrl = getChampionIconUrl(item);
      row.innerHTML = `
        <span class="tag-row__index">${index + 1}</span>
        ${avatarUrl ? `<img class="tag-row__avatar" src="${avatarUrl}" alt="${item}" />` : ""}
        <span class="tag-row__label">${item}</span>
      `;
      root.appendChild(row);
    });
    return;
  }

  if (!warning) {
    root.innerHTML = '<div class="empty-state">Sem observacoes extras.</div>';
  }
}

function activateTagFilter(tag) {
  const nextTag = isTagActive(tag) ? "" : tag;
  state.tag = nextTag;
  els.tagSelect.value = nextTag;
  applyFilters();
  renderTagCloud();
  renderChampions();
  if (els.catalogPanel) {
    els.catalogPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function clearTagFilter() {
  state.tag = "";
  els.tagSelect.value = "";
  applyFilters();
  renderTagCloud();
  renderChampions();
}

function isTagActive(tag) {
  return normalizeText(state.tag) === normalizeText(tag);
}

function countChampionsByTag(tag) {
  const normalizedTag = normalizeText(tag);
  return state.champions.filter((champion) =>
    champion.tags.some((championTag) => normalizeText(championTag) === normalizedTag),
  ).length;
}

function compareTagPriority(left, right, normalizedTag) {
  if (!normalizedTag) {
    return 0;
  }

  const leftMatches = left.tags.some((tag) => normalizeText(tag) === normalizedTag);
  const rightMatches = right.tags.some((tag) => normalizeText(tag) === normalizedTag);

  if (leftMatches === rightMatches) {
    return 0;
  }

  return leftMatches ? -1 : 1;
}

function compareSearchPriority(left, right, normalizedSearch) {
  const leftScore = getSearchPriority(left, normalizedSearch);
  const rightScore = getSearchPriority(right, normalizedSearch);
  if (leftScore !== rightScore) {
    return leftScore - rightScore;
  }
  return 0;
}

function getSearchPriority(champion, normalizedSearch) {
  if (!normalizedSearch) {
    return 99;
  }

  const fields = [
    normalizeText(champion.name),
    normalizeText(champion.riot_id),
    normalizeText(String(champion.key)),
  ];

  if (fields.some((field) => field === normalizedSearch)) {
    return 0;
  }
  if (fields.some((field) => field.startsWith(normalizedSearch))) {
    return 1;
  }
  if (fields.some((field) => field.includes(normalizedSearch))) {
    return 2;
  }
  return 3;
}

function getChampionSplashUrl(championName) {
  const champion = state.champions.find(
    (item) =>
      normalizeText(item.name) === normalizeText(championName) ||
      normalizeText(item.riot_id) === normalizeText(championName),
  );

  if (!champion) {
    return null;
  }

  return `https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${champion.riot_id}_0.jpg`;
}

function getChampionIconUrl(championName) {
  const champion = state.champions.find(
    (item) =>
      normalizeText(item.name) === normalizeText(championName) ||
      normalizeText(item.riot_id) === normalizeText(championName),
  );

  return champion ? champion.icon_url : null;
}

function applySuggestionArt(card, imageUrl) {
  const bg = card.querySelector(".recommendation-card__bg");
  if (!imageUrl) {
    bg.style.backgroundImage = "";
    card.classList.remove("has-art");
    return;
  }

  bg.style.backgroundImage = `url("${imageUrl}")`;
  card.classList.add("has-art");
}

function getRoleInput(role) {
  return {
    top: els.enemyTop,
    jungler: els.enemyJungler,
    mid: els.enemyMid,
    carry: els.enemyCarry,
    sup: els.enemySup,
  }[role];
}

function bindComboboxEvents() {
  els.comboboxes.forEach((combobox) => {
    const input = combobox.querySelector(".combobox__input");
    const toggle = combobox.querySelector(".combobox__toggle");

    input.addEventListener("focus", () => {
      openCombobox(combobox);
      renderComboboxOptions(combobox);
    });

    input.addEventListener("input", () => {
      openCombobox(combobox);
      renderComboboxOptions(combobox);
    });

    input.addEventListener("keydown", (event) => handleComboboxKeydown(event, combobox));

    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      if (combobox.classList.contains("is-open")) {
        closeCombobox(combobox);
        return;
      }
      openCombobox(combobox);
      input.focus();
      renderComboboxOptions(combobox);
    });
  });
}

function renderComboboxOptions(combobox) {
  const input = combobox.querySelector(".combobox__input");
  const menu = combobox.querySelector(".combobox__menu");
  const filter = normalizeText(input.value);
  const items = state.guideChampionNames.filter((champion) => {
    return !filter || normalizeText(champion).includes(filter);
  });

  menu.innerHTML = "";

  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "combobox__empty";
    empty.textContent = "Nenhum campeao encontrado.";
    menu.appendChild(empty);
    combobox.dataset.activeIndex = "-1";
    return;
  }

  items.forEach((champion, index) => {
    const option = document.createElement("button");
    option.type = "button";
    option.className = "combobox__option";
    option.dataset.index = String(index);
    option.dataset.value = champion;
    option.innerHTML = `
      <span class="combobox__option-label">${champion}</span>
    `;
    option.addEventListener("mouseenter", () => setActiveOption(combobox, index));
    option.addEventListener("click", () => selectComboboxOption(combobox, champion));
    menu.appendChild(option);
  });

  const exactMatchIndex = items.findIndex((champion) => normalizeText(champion) === filter);
  const activeIndex = exactMatchIndex >= 0 ? exactMatchIndex : 0;
  combobox.dataset.activeIndex = String(Math.min(activeIndex, menu.children.length - 1));
  syncActiveOption(combobox);
}

function handleComboboxKeydown(event, combobox) {
  const hasOptions = combobox.querySelectorAll(".combobox__option").length > 0;

  if (event.key === "ArrowDown") {
    event.preventDefault();
    if (!combobox.classList.contains("is-open")) {
      openCombobox(combobox);
      renderComboboxOptions(combobox);
      return;
    }
    if (hasOptions) {
      moveActiveOption(combobox, 1);
    }
    return;
  }

  if (event.key === "ArrowUp") {
    event.preventDefault();
    if (hasOptions) {
      moveActiveOption(combobox, -1);
    }
    return;
  }

  if (event.key === "Enter") {
    if (!combobox.classList.contains("is-open")) {
      return;
    }
    event.preventDefault();
    const active = combobox.querySelector(".combobox__option.is-active");
    if (active) {
      selectComboboxOption(combobox, active.dataset.value || "");
    }
    return;
  }

  if (event.key === "Escape") {
    closeCombobox(combobox);
  }
}

function handleDocumentClick(event) {
  const target = event.target;
  const clickedCombobox = target.closest(".combobox");
  const clickedSearchbox = target.closest(".searchbox");
  if (clickedCombobox) {
    return;
  }
  if (!clickedSearchbox) {
    closeSearchSuggestions();
  }
  closeAllComboboxes();
}

function handleGlobalKeydown(event) {
  if (event.key === "Escape") {
    closeAllComboboxes();
  }
}

function handleWindowScroll() {
  updateSectionNavigation();
  updateBackToTopButton();
}

function updateSectionNavigation() {
  if (!els.heroNavLinks.length) {
    return;
  }

  const sections = els.heroNavLinks
    .map((link) => {
      const hash = link.getAttribute("href");
      if (!hash || !hash.startsWith("#")) {
        return null;
      }
      return {
        link,
        section: document.querySelector(hash),
      };
    })
    .filter(Boolean)
    .filter((item) => item.section);

  if (!sections.length) {
    return;
  }

  const threshold = window.scrollY + 180;
  let active = sections[0];

  sections.forEach((item) => {
    if (item.section.offsetTop <= threshold) {
      active = item;
    }
  });

  sections.forEach((item) => {
    item.link.classList.toggle("is-active", item === active);
  });
}

function updateBackToTopButton() {
  if (!els.backToTopButton) {
    return;
  }
  els.backToTopButton.classList.toggle("is-visible", window.scrollY > 360);
}

function openCombobox(combobox) {
  closeAllComboboxes(combobox);
  const menu = combobox.querySelector(".combobox__menu");
  combobox.classList.add("is-open");
  menu.hidden = false;
}

function closeCombobox(combobox) {
  const menu = combobox.querySelector(".combobox__menu");
  combobox.classList.remove("is-open");
  menu.hidden = true;
}

function closeAllComboboxes(exceptCombobox = null) {
  els.comboboxes.forEach((combobox) => {
    if (combobox === exceptCombobox) {
      return;
    }
    closeCombobox(combobox);
  });
}

function selectComboboxOption(combobox, value) {
  const input = combobox.querySelector(".combobox__input");
  input.value = value;
  renderComboboxOptions(combobox);
  closeCombobox(combobox);
}

function moveActiveOption(combobox, step) {
  const options = Array.from(combobox.querySelectorAll(".combobox__option"));
  if (!options.length) {
    return;
  }

  const current = Number(combobox.dataset.activeIndex || 0);
  const next = Math.max(0, Math.min(options.length - 1, current + step));
  setActiveOption(combobox, next);
}

function setActiveOption(combobox, index) {
  combobox.dataset.activeIndex = String(index);
  syncActiveOption(combobox);
}

function syncActiveOption(combobox) {
  const options = Array.from(combobox.querySelectorAll(".combobox__option"));
  const activeIndex = Number(combobox.dataset.activeIndex || -1);

  options.forEach((option, index) => {
    option.classList.toggle("is-active", index === activeIndex);
  });

  const activeOption = options[activeIndex];
  if (activeOption) {
    activeOption.scrollIntoView({ block: "nearest" });
  }
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = "Requisicao falhou.";
    try {
      const payload = await response.json();
      detail = payload.detail || JSON.stringify(payload);
    } catch (_) {
      detail = await response.text();
    }
    throw new Error(detail);
  }
  return response.json();
}

function normalizeText(value) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase();
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.className = `toast${isError ? " toast--error" : ""}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  window.setTimeout(() => toast.remove(), 3400);
}

function formatPercent(value) {
  return typeof value === "number" ? `${value.toFixed(1)}%` : "-";
}

function buildRecommendationShareText(data = state.recommendation) {
  if (!data) {
    return "Monte o time inimigo para gerar um resumo compartilhavel do draft.";
  }

  const lanes = [
    ["Top", els.enemyTop.value.trim()],
    ["Jungler", els.enemyJungler.value.trim()],
    ["Mid", els.enemyMid.value.trim()],
    ["Carry", els.enemyCarry.value.trim()],
    ["Sup", els.enemySup.value.trim()],
  ]
    .filter(([, value]) => value)
    .map(([label, value]) => `${label}: ${value}`)
    .join(" | ");

  const adc = data.suggested_adc
    ? `${data.suggested_adc.champion} (${data.suggested_adc.votes} voto(s))`
    : "Sem sugestao";
  const support = data.suggested_support
    ? `${data.suggested_support.champion} (${data.suggested_support.votes} voto(s))`
    : "Sem sugestao";

  return `Time inimigo: ${lanes || "nao informado"}\nADC sugerido: ${adc}\nSuporte sugerido: ${support}`;
}

async function copyDraftSummary() {
  const text = buildRecommendationShareText();
  try {
    await navigator.clipboard.writeText(text);
    showToast("Resumo do draft copiado.");
  } catch (error) {
    showToast("Nao foi possivel copiar automaticamente.", true);
  }
}

async function shareDraftSummary() {
  const text = buildRecommendationShareText();
  try {
    if (navigator.share) {
      await navigator.share({
        title: "LoL Counter Picker",
        text,
      });
      return;
    }
    await navigator.clipboard.writeText(text);
    showToast("Seu navegador nao suporta compartilhamento direto. O resumo foi copiado.");
  } catch (error) {
    if (error && error.name === "AbortError") {
      return;
    }
    showToast("Nao foi possivel compartilhar o resumo.", true);
  }
}
