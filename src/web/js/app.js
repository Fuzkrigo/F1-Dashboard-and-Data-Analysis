/**
 * F1 Insights Engine - Frontend Logic
 *
 * [EN] Manages the Single Page Application (SPA) routing,
 * data fetching, and Plotly charts rendering with XSS mitigation.
 *
 * [PT-BR] Gerencia o roteamento da Single Page Application (SPA),
 * a busca de dados na API e a renderização dos gráficos com mitigação XSS.
 *
 * Author: Bruno Krieger
 */
import { API_BASE } from './config.js';
import { getTeamColor } from './lib/teamColors.js';
import { escapeHTML, formatLapTime, clampDec } from './lib/format.js';
import { calcStats } from './lib/stats.js';

// DOM Elements
const seasonSelect = document.getElementById('season-select');
const navLinks = document.querySelectorAll('.nav-links li');
const views = document.querySelectorAll('.view');
const pageTitle = document.getElementById('page-title');
const headerKanji = document.getElementById('header-kanji');

// State
let currentSeason = null;

// Routing titles
/**
 * Views configuration mapping.
 * [PT-BR] Mapeamento de configuração das telas.
 */
const viewMeta = {
    'overview': { title: 'VISÃO GERAL DO CAMPEONATO' },
    'telemetry': { title: 'TELEMETRIA E RITMO' },
    'evolution': { title: 'EVOLUÇÃO DO CAMPEONATO' },
    'h2h': { title: 'BATALHA HEAD-TO-HEAD' },
    'pits': { title: 'ANÁLISE DE PIT STOPS' },
    'grid': { title: 'DOMÍNIO DE PISTA' },
    'history': { title: 'ARQUIVO HISTÓRICO' }
};

// ============================================================================
// getTeamColor e escapeHTML movidos para ./lib/teamColors.js e ./lib/format.js
// (importados no topo deste arquivo).
// ============================================================================

// ============================================================================
// Custom Global Tooltip Engine (F1 Engine Unified Replacement)
// ============================================================================

/**
 * Exibe programaticamente a tooltip em formato HTML.
 * @param {Event} e - O raw pointer event do Plotly para capturar coordenadas (x,y) do mouse
 * @param {String} title - Título da Tooltip (ex: 'R1 - Bahrain' ou 'Volta 12')
 * @param {Array} rows - Array de objetos: { color, name, value, sortValue }
 */
function showCustomTooltip(e, title, rows) {
    const tooltip = document.getElementById('f1-custom-tooltip');
    if (!tooltip) return;

    // Constrói o HTML Linha a Linha
    let htmlContent = '';
    if (title) {
        htmlContent += `<div class="tooltip-title">${title}</div>`;
    }

    rows.forEach(r => {
        htmlContent += `
        <div class="tooltip-row">
            <span class="tooltip-name" style="color: ${r.color};">
              <span class="tooltip-color-indicator" style="background-color: ${r.color};"></span>
              ${r.name}
            </span>
            <span class="tooltip-value">${r.value}</span>
        </div>`;
    });

    tooltip.innerHTML = htmlContent;

    // Posicionamento dinâmico (com offset para evitar mouse colidindo na caixa)
    const mouseX = e.clientX;
    const mouseY = e.clientY;
    const offset = 15;

    // Limites da Janela para tooltip não quebrar fora da tela
    let posX = mouseX + offset;
    let posY = mouseY + offset;

    const tooltipRect = tooltip.getBoundingClientRect();
    if (posX + tooltipRect.width > window.innerWidth) {
        posX = mouseX - tooltipRect.width - offset;
    }
    if (posY + tooltipRect.height > window.innerHeight) {
        posY = mouseY - tooltipRect.height - offset;
    }

    tooltip.style.left = `${posX}px`;
    tooltip.style.top = `${posY}px`;
    tooltip.style.display = 'block';
    tooltip.style.opacity = '1';
}

function hideCustomTooltip() {
    const tooltip = document.getElementById('f1-custom-tooltip');
    if (tooltip) {
        tooltip.style.opacity = '0';
        setTimeout(() => { if(tooltip.style.opacity === '0') tooltip.style.display = 'none'; }, 100);
    }
}

/**
 * Conecta o Hover Dinâmico Personalizado HTML num dado gráfico Plotly.
 * Esta função deve ser chamada logo após Plotly.newPlot.
 */
function bindCustomTooltip(chartId, titleMode = 'x', titleFormatter = (x)=>x, valueFormatter = (val, pt)=>val) {
    const chart = document.getElementById(chartId);
    if (!chart) return;

    // 1. Forçar Hoverinfo para none de todos os traces do gráfico e desativar spikelines invasivos
    Plotly.restyle(chartId, { hoverinfo: 'none' });

    // 2. Ouvir plotly_hover
    chart.on('plotly_hover', function(data) {
        if (!data || !data.points || data.points.length === 0) return;

        // Radar charts (scatterpolar) natively only return the hovered trace even with unified mode.
        // We intercept and rebuild `data.points` to gather all traces at that theta.
        if (data.points[0].data && data.points[0].data.type === 'scatterpolar') {
            const hoveredTheta = data.points[0].theta;
            const newPoints = [];
            chart.data.forEach((trace, traceIndex) => {
                if (trace.type === 'scatterpolar' && trace.theta) {
                    const tIndex = trace.theta.indexOf(hoveredTheta);
                    if (tIndex !== -1) {
                        newPoints.push({
                            data: trace,
                            pointIndex: tIndex,
                            r: trace.r[tIndex],
                            theta: trace.theta[tIndex],
                            color: trace.line?.color || trace.marker?.color || '#FFF'
                        });
                    }
                }
            });
            data.points = newPoints;
        }

        // Pegamos o X do primeiro ponto intersectado para ser o título geral
        let mainX = data.points[0].x !== undefined ? data.points[0].x : data.points[0].theta;
        let title = `${titleFormatter(mainX)}`;

        let rows = [];

        // Montar linhas de dado baseada nos points que estão no eixo X tocado
        data.points.forEach(pt => {
            // Em gráficos complexos The object name is mostly in data.name
            let ptName = pt.data.name || 'Série';
            // Plotly injeta <span style="..."> no .name anterior nosso, vamos limpar o html se houver para usar direto
            ptName = ptName.replace(/<\/?[^>]+(>|$)/g, "");

            let color = pt.data.line?.color || pt.data.marker?.color || pt.color || '#FFF';

            // Tratamento especial para arrays de cores (ex: bars e scatters de categorias)
            if (Array.isArray(color)) {
                color = color[pt.pointIndex] || '#FFF';
            }

            // pt.text em eventos Plotly refere-se ao texto daquele ponto exato
            let hoverText = Array.isArray(pt.text) ? pt.text[pt.pointIndex] : pt.text;

            // Radar charts perdem referencia posicional em hoverText (costuma vir undefined e quebrar o parse string)
            if (pt.data && pt.data.type === 'scatterpolar') {
                hoverText = undefined;
            }

            let valueStr = hoverText !== undefined ? String(hoverText) : String(pt.y);
            let sortValue = Number(pt.y);

            // Casos Radiais / Horizontais (Inversão X e Y)
            if (pt.data && pt.data.orientation === 'h') {
                valueStr = hoverText !== undefined ? String(hoverText) : String(pt.x);
                sortValue = Number(pt.x);
                title = String(pt.y); // Se é barra H, o titulo que agrupam elas é o Y
            } else if (pt.data && pt.data.type === 'scatterpolar') {
                valueStr = typeof pt.r === 'number' ? pt.r.toFixed(1) : String(pt.r);
                sortValue = Number(pt.r) || 0;
                title = String(pt.theta);
            }

            valueStr = valueFormatter(valueStr, pt);

            rows.push({
                color: color,
                name: ptName,
                value: valueStr,
                sortValue: sortValue
            });
        });

        // O SEGREDO DO PEDIDO: ORDENAR A LISTA PELO VALOR DECRESCENTE (DO MAIOR PARA O MENOR NAQUELE EXATO PONTO)
        rows.sort((a,b) => b.sortValue - a.sortValue);

        showCustomTooltip(data.event, title, rows);
    });

    // 3. Ouvir plotly_unhover
    chart.on('plotly_unhover', function() {
        hideCustomTooltip();
    });
}
// ============================================================================
// Initialization / Inicialização
// ============================================================================
document.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch available seasons
    await loadSeasons();

    // 2. Setup navigation listeners
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const viewId = link.getAttribute('data-view');
            navigateTo(viewId, link);
        });
    });

    // 3. Setup global filters listener
    seasonSelect.addEventListener('change', (e) => {
        currentSeason = e.target.value;
        refreshCurrentView();
    });
});

async function loadSeasons() {
    try {
        const response = await fetch(`${API_BASE}/seasons/?limit=100&populated_only=true`);
        const seasons = await response.json();

        seasonSelect.innerHTML = '';

        if (!seasons || seasons.length === 0) {
            seasonSelect.innerHTML = '<option disabled>Nenhum dado...</option>';
            return;
        }

        // We assume all seasons in the DB are valid to prevent 75+ sequential requests freezing the DOM
        const validSeasons = seasons;

        // Sort descending
        validSeasons.sort((a,b) => b.year - a.year);

        validSeasons.forEach(s => {
            const option = document.createElement('option');
            option.value = s.year;
            option.textContent = `${s.year} Season`;
            seasonSelect.appendChild(option);
        });

        // Selecionar sempre a temporada mais atual (maior ano) já ordenado em validSeasons
        currentSeason = validSeasons[0].year;
        seasonSelect.value = currentSeason;

        // Trigger load of the default view (overview)
        refreshCurrentView();

    } catch (error) {
        console.error("Erro ao carregar temporadas:", error);
        seasonSelect.innerHTML = '<option disabled>API Offline</option>';
        document.getElementById('kpi-races').textContent = "ERROR";
        document.getElementById('kpi-races').style.fontSize = "1.5rem";
    }
}

// ============================================================================
// Navigation Logic
// ============================================================================
function navigateTo(viewId, clickedLinkElement) {
    // Update active nav link
    navLinks.forEach(el => el.classList.remove('active'));
    clickedLinkElement.classList.add('active');

    // Update active view
    views.forEach(view => {
        view.classList.remove('active');
        if (view.id === `view-${viewId}`) {
            view.classList.add('active');
        }
    });

    // Update Headers
    pageTitle.textContent = viewMeta[viewId].title;

    refreshCurrentView();
}

function refreshCurrentView() {
    const activeLink = document.querySelector('.nav-links li.active');
    if (!activeLink) return;

    const viewId = activeLink.getAttribute('data-view');

    if (viewId === 'overview') loadOverview(currentSeason);
    else if (viewId === 'telemetry') loadTelemetry(currentSeason);
    else if (viewId === 'evolution') loadEvolution(currentSeason);
    else if (viewId === 'h2h') loadH2H(currentSeason);
    else if (viewId === 'pits') loadPits(currentSeason);
    else if (viewId === 'grid') loadGrid(currentSeason);
    else if (viewId === 'history') loadHistory(currentSeason);
}

// ============================================================================
// API Fetch Helpers
// ============================================================================
async function fetchAPI(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`);
    if (!res.ok) throw new Error(`API returned ${res.status}`);
    return res.json();
}

// ============================================================================
// View Controllers / Controladores de Visualização
// ============================================================================

/**
 * [EN] Loads and renders the Overview panel (KPIs and Charts).
 * [PT-BR] Carrega e renderiza o painel de Visão Geral (KPIs e Gráficos).
 * @param {number} season - The selected season year / O ano da temporada.
 */
// 1. Overview Controller
async function loadOverview(season) {
    try {
        // Fetch races for count
        const races = await fetchAPI(`/races/?season=${season}&limit=100`);
        document.getElementById('kpi-races').textContent = races.length;

        // Fetch standings
        const driverSt = await fetchAPI(`/standings/drivers/?season=${season}`);
        const constructorSt = await fetchAPI(`/standings/constructors/?season=${season}`);

        // Update Driver Leader KPI (nome/codigo ja vem no standing enriquecido)
        if (driverSt.length > 0) {
            const leaderD = driverSt[0];
            const leaderLabel = leaderD.driver_code || leaderD.driver_name || '';
            document.getElementById('kpi-driver-leader').textContent = escapeHTML(leaderLabel).toUpperCase();
            document.getElementById('kpi-driver-points').textContent = `${leaderD.points} pts`;
        } else {
            document.getElementById('kpi-driver-leader').textContent = "--";
            document.getElementById('kpi-driver-points').textContent = "-- pts";
        }

        // Update Constructor Leader KPI (constructor_name ja vem no standing enriquecido)
        if (constructorSt.length > 0) {
            const leaderC = constructorSt[0];
            document.getElementById('kpi-team-leader').textContent = escapeHTML(leaderC.constructor_name || '').toUpperCase();
            document.getElementById('kpi-team-points').textContent = `${leaderC.points} pts`;
        } else {
            document.getElementById('kpi-team-leader').textContent = "--";
            document.getElementById('kpi-team-points').textContent = "-- pts";
        }

        // Plotly Charts - All Drivers
        if (driverSt.length > 0) {
            // Nome e equipe ja vem no standing enriquecido -> sem requisicao por piloto
            driverSt.forEach((st) => {
                const permNum = st.permanent_number ? ` - ${st.permanent_number}` : '';
                st.driverName = escapeHTML(`${st.driver_name}${permNum}`);
                st.teamColor = getTeamColor(st.constructor_name);
            });

            // Note: Não aplicaremos sort() alfabético aqui, manteremos a ordem natural do campeonato vinda da API (Ranked)

            const maxDriversPoints = driverSt.length > 0 ? Math.max(...driverSt.map(d => d.points)) : 100;

            const traceDrivers = {
                x: driverSt.map(d => d.points),
                y: driverSt.map(d => d.driverName),
                type: 'bar',
                orientation: 'h',
                name: 'Pontuação de Pilotos',
                text: driverSt.map((d, i) => i === 0 ? `  ${d.points} PTS` : ''), // Exibe pontos do primeiro colocado
                textposition: 'outside',
                cliponaxis: false,
                marker: { color: driverSt.map(d => d.teamColor) } // Dinâmico pela equipe
            };
            const layoutDrivers = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#8AA4C8', family: 'Orbitron' },
                margin: { t: 20, b: 40, l: 10, r: 40 }, // L:10 garante ancoragem EXTREMA ao Lado Esquerdo da tela
                xaxis: {
                    range: [0, maxDriversPoints * 1.20] // Folga extra real empurrando o limite da tela para evitar corrompimento da string
                },
                yaxis: {
                    autorange: 'reversed', // Mantém o campeão no topo
                    automargin: true,      // Calcula a responsividade e estica o nome apenas pelo tanto que ele precisa
                    ticksuffix: '      ',  // Recuo (espaçadores) reais empurrando a barra para a direita e livrando o nome
                    ticklabelposition: "outside left" // Teta forçar alinhamento explícito ao limite máximo esquero do DOM
                }
            };
            Plotly.newPlot('overview-chart-drivers', [traceDrivers], layoutDrivers, {displayModeBar: false, responsive: true});
            bindCustomTooltip('overview-chart-drivers', 'y', (y) => y, (val) => val + ' pts');
        }

        // Plotly Charts - Teams
        if (constructorSt.length > 0) {
            // constructor_name ja vem inline -> sem requisicao por equipe
            constructorSt.forEach((st) => {
                st.teamName = escapeHTML(st.constructor_name || '');
            });

            const maxTeamsPoints = constructorSt.length > 0 ? Math.max(...constructorSt.map(c => c.points)) : 100;

            const traceTeams = {
                x: constructorSt.map(c => c.points),
                y: constructorSt.map(c => c.teamName),
                type: 'bar',
                orientation: 'h',
                name: 'Pontuação de Construtores',
                text: constructorSt.map((c, i) => i === 0 ? `  ${c.points} PTS` : ''), // Exibe pontos do campeonato para a Equipe Líder
                textposition: 'outside',
                cliponaxis: false,
                marker: {
                    color: constructorSt.map(c => getTeamColor(c.teamName))
                }
            };
            const layoutTeams = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#8AA4C8', family: 'Orbitron' },
                margin: { t: 20, b: 40, l: 10, r: 40 },
                xaxis: {
                    range: [0, maxTeamsPoints * 1.20] // Folga de 20% barrando o corte do valor
                },
                yaxis: {
                    autorange: 'reversed',
                    automargin: true,
                    ticksuffix: '      ',
                    ticklabelposition: "outside left"
                }
            };
            Plotly.newPlot('overview-chart-teams', [traceTeams], layoutTeams, {displayModeBar: false, responsive: true});
            bindCustomTooltip('overview-chart-teams', 'y', (y) => y, (val) => val + ' pts');
        }

    } catch(e) { console.error(e); }
}

// 2. Telemetry Controller (FastF1 Advanced API)
async function loadTelemetry(season) {
    try {
        const racesSelect = document.getElementById('telemetry-race');
        const driver1Select = document.getElementById('telemetry-driver1');
        const driver2Select = document.getElementById('telemetry-driver2');
        const loader = document.getElementById('telemetry-loader');
        const dashContainer = document.getElementById('telemetry-dash-container');

        racesSelect.innerHTML = '<option value="" disabled selected>Carregando Corridas...</option>';

        // Busca corridas da temporada
        const races = await fetchAPI(`/races/?season=${season}&limit=100`);
        if (races.length === 0) {
            racesSelect.innerHTML = '<option disabled>Sem Corridas</option>';
            return;
        }

        races.sort((a,b) => a.round - b.round);
        racesSelect.innerHTML = '<option value="" disabled selected>Selecione a Corrida...</option>';
        races.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.round; // IMPORTANTE: Passamos Round NUM para o FastF1
            opt.textContent = `R${r.round} - ${r.race_name || 'Corrida'}`;
            racesSelect.appendChild(opt);
        });

        // Configurar dropdowns de pilotos baseados na temporada e classificação (para ter top drivers)
        const standings = await fetchAPI(`/standings/drivers/?season=${season}`);
        const listDrivers = standings.length > 0 ? standings : [];

        // Seletores Antigos Extintos. Pegar Container de Toggles e Botão Gerar
        const togglesContainer = document.getElementById('driver-toggles-container');
        const btnGenerate = document.getElementById('btn-generate-telemetry');

        // Limpar container e adicionar estado de loading
        togglesContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem;">Processando Grid F1...</div>';

        // Popular options
        await Promise.all(listDrivers.map(async (s) => {
            try {
                // driver_code e driver_name ja vem no standing enriquecido -> sem requisicao por piloto
                const code3 = s.driver_code || (s.driver_name ? s.driver_name.substring(0, 3).toUpperCase() : 'N/A');

                // HTML Baseado em Label/Checkbox escondido p/ toggle visual puro (Sci-fi)
                s.optionHTML = `
                    <label class="driver-toggle-label hud-bracket" style="
                        display: inline-block;
                        flex: 1;
                        text-align: center;
                        padding: 6px 4px;
                        cursor: pointer;
                        background: rgba(11, 20, 38, 0.6);
                        border: 1px solid var(--border-color);
                        color: var(--text-muted);
                        font-family: var(--font-header);
                        font-size: 0.75rem;
                        transition: all 0.2s;
                        user-select: none;
                    ">
                        <input type="checkbox" value="${code3}" data-name="${s.driver_name}" data-team="" style="display: none;" onchange="
                           if(this.checked) {
                               this.parentElement.style.background = 'rgba(0, 240, 255, 0.2)';
                               this.parentElement.style.borderColor = 'var(--accent-cyan)';
                               this.parentElement.style.color = '#FFF';
                               this.parentElement.style.textShadow = '0 0 5px var(--accent-cyan)';
                           } else {
                               this.parentElement.style.background = 'rgba(11, 20, 38, 0.6)';
                               this.parentElement.style.borderColor = 'var(--border-color)';
                               this.parentElement.style.color = 'var(--text-muted)';
                               this.parentElement.style.textShadow = 'none';
                           }
                        ">
                        ${code3}
                    </label>
                `;
                s.sortName = s.driver_name || 'ZZZ';
            } catch (err) {
                console.error("Error fetching driver:", s.driver_id, err);
                s.optionHTML = '';
                s.sortName = 'ZZZ';
            }
        }));

        // Ordenar os pilotos por ordem alfabética do nome formatado
        listDrivers.sort((a,b) => a.sortName.localeCompare(b.sortName));

        // Injetar HTML Gerado no Container
        togglesContainer.innerHTML = '';
        listDrivers.forEach(s => {
            if(s.optionHTML) {
                 togglesContainer.insertAdjacentHTML('beforeend', s.optionHTML);
            }
        });

        // Define the auto-loading function on Button Click
        const generateMultiTelemetry = async () => {
            const roundNum = racesSelect.value;

            // Buscar todos os checkboxes que o usuário marcou como 'checked'
            const checkedBoxes = Array.from(togglesContainer.querySelectorAll('input[type="checkbox"]:checked'));
            const selectedCodes = checkedBoxes.map(cb => cb.value);

            if (!roundNum) {
                alert("Selecione primeiramente a Corrida no menu suspenso.");
                return;
            }

            if (selectedCodes.length === 0) {
                alert("Você deve selecionar pelo menos 1 (um) piloto clicando nos botões da grade.");
                return;
            }

            // Exibir Loader (FastF1 primeiro cache demora)
            loader.style.display = 'block';

            // NÃO usar display: none! Mantenha a caixa ocupando 100% da tela fisicamente para preservar a geometria CSS. Traz o loader visualmente.
            dashContainer.style.opacity = '0.3';
            if (dashContainer.style.display === 'none') dashContainer.style.display = 'block';

            try {
                // Build dynamic Querystring parameter array for N-drivers
                const sessionType = document.getElementById('telemetry-session').value;
                let url = `/telemetry/?year=${season}&round_num=${roundNum}&session_type=${sessionType}`;
                selectedCodes.forEach(code => {
                    url += `&drivers=${code}`;
                });

                const data = await fetchAPI(url);

                // --- 1. Atualizar KPIs ---
                const kpiRow = document.getElementById('tel-kpi-row');
                kpiRow.innerHTML = ''; // Clear existing layout

                // Arrays p/ os Traces dos gráficos que serão preenchidos
                const tracesLap = [];

                // formatLapTime e clampDec importados de ./lib/format.js

                // Iterar Linearmente sobre a resposta N-pilotos da API
                Object.values(data.drivers).forEach((driverData) => {
                    const tColor = getTeamColor(driverData.team);

                    // 1. Encontrar o número da volta mais rápida
                    const lapTimes = driverData.lap_chart.lap_time;
                    const lapNums = driverData.lap_chart.lap_number;
                    let fastestIdx = 0;
                    for (let i = 1; i < lapTimes.length; i++) {
                        if (lapTimes[i] != null && (lapTimes[fastestIdx] == null || lapTimes[i] < lapTimes[fastestIdx])) {
                            fastestIdx = i;
                        }
                    }
                    const fastestLapNum = lapNums[fastestIdx];

                    // 2. Injetar Caixa HTML Dinâmica do KPI (clicável)
                    const kpiCard = `
                        <div class="kpi-card glass-panel hud-bracket" style="border-top: 3px solid ${tColor}; flex: 0 0 367px; cursor: pointer; transition: box-shadow 0.2s; padding: 10px; text-align: center;"
                             onclick="window.selectFastestLap('${driverData.name}', ${fastestLapNum}, '${tColor}')"
                             onmouseover="this.style.boxShadow='0 0 12px ${tColor}'" onmouseout="this.style.boxShadow='none'"
                             title="Clique para ver a telemetria da volta mais rápida">
                            <div class="kpi-label">${driverData.name}</div>
                            <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">Volta Rápida (L${fastestLapNum})</div>
                            <div class="kpi-value" style="color: ${tColor}; font-size: 1.5rem;">${driverData.fastest_lap_time.replace(/(\.\d{3})\d*/, '$1')}</div>
                            <div class="kpi-subvalue">Composto: <span>${driverData.compound}</span></div>
                        </div>
                    `;
                    kpiRow.insertAdjacentHTML('beforeend', kpiCard);

                    // 2. Preencher Traces do LAP CHART com pt.text para o Custom Tooltip interceptar
                    tracesLap.push({
                        x: driverData.lap_chart.lap_number,
                        y: driverData.lap_chart.lap_time,
                        text: driverData.lap_chart.lap_time.map((t, i) => {
                            const comp = driverData.lap_chart.compound[i];
                            return `${formatLapTime(t)} (${comp})`;
                        }),
                        mode: 'lines+markers',
                        name: `<span style="color: ${tColor}">${driverData.name}</span>`,
                        line: { color: tColor, width: 2 },
                        marker: { size: 6 }
                    });

                    // 3. ANÁLISE DETALHADA — NÃO plotar automaticamente.
                    //    O Detail Chart é preenchido sob demanda via clique no Lap Chart.
                });

                // --- 2. Plotar Rastreador de Circuito (Map) ---
                const rawX = data.track_map.x;
                const rawY = data.track_map.y;

                const xMin = Math.min(...rawX), xMax = Math.max(...rawX);
                const yMin = Math.min(...rawY), yMax = Math.max(...rawY);
                const xRange = xMax - xMin;
                const yRange = yMax - yMin;

                let plotX = clampDec(rawX);
                let plotY = clampDec(rawY);

                // Se o circuito for muito "vertical", o deitamos girando 90 graus para aproveitar a tela horizontal
                if (yRange > xRange) {
                    plotX = rawY;
                    plotY = rawX.map(x => -x);
                }

                const traceMap = {
                    x: plotX,
                    y: plotY,
                    mode: 'lines',
                    line: { color: 'rgba(255,255,255,0.8)', width: 4 },
                    name: 'Track'
                };

                // Marcar posição (0,0) aproximada do Start
                const startPoint = {
                    x: [plotX[0]],
                    y: [plotY[0]],
                    mode: 'markers',
                    marker: { size: 12, color: '#00F0FF', symbol: 'star' },
                    name: 'Finish Line'
                };

                const layoutMap = {
                    height: 500,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    margin: { t: 40, b: 40, l: 40, r: 40 },
                    xaxis: { visible: false, showgrid: false, zeroline: false },
                    yaxis: { visible: false, scaleanchor: "x", scaleratio: 1, showgrid: false, zeroline: false },
                    showlegend: false,
                    autosize: true
                };

                const layoutLap = {
                    height: 500,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#8AA4C8', family: 'Orbitron' },
                    margin: { t: 40, b: 40, l: 60, r: 20 },
                    xaxis: {
                        title: 'Volta',
                        gridcolor: '#1A2C42',
                        showspikes: true,
                        spikemode: 'across',
                        spikesnap: 'cursor',
                        showline: true,
                        spikecolor: 'rgba(0, 240, 255, 0.15)',
                        spikethickness: 1,
                        spikedash: 'dash'
                    },
                    yaxis: { title: 'Tempo (segundos)', gridcolor: '#1A2C42' },
                    legend: { orientation: 'h', y: 1.1, x: 0 },
                    autosize: true
                };

                // --- 3. Exibir o Dashboard (Após Plotar - Restaurar Transparência) ---
                loader.style.display = 'none';
                dashContainer.style.opacity = '1';

                // PURGE de quadros antigos
                Plotly.purge('telemetry-map-chart');
                Plotly.purge('telemetry-detail-chart');
                Plotly.purge('telemetry-lap-chart');

                // Resetar o painel de voltas selecionadas
                const selectedLapsPanel = document.getElementById('selected-laps-panel');
                selectedLapsPanel.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem;" id="no-laps-msg">Nenhuma volta selecionada. Clique nos pontos do Lap Chart ↑</span>';
                document.getElementById('telemetry-detail-chart').style.display = 'none';

                // Estado global de voltas selecionadas para esta sessão de telemetria
                window._selectedLaps = [];
                window._driverTeamMap = {};

                // Mapear cor de cada piloto carregado para uso nos traces
                Object.values(data.drivers).forEach((d) => {
                    window._driverTeamMap[d.name] = { team: d.team, color: getTeamColor(d.team) };
                });

                // Guardar contexto da sessão atual para o fetch de /telemetry/lap/
                window._telemetryContext = { season, roundNum, sessionType };

                // Renderizar Lap Chart e Map
                setTimeout(() => {
                    Plotly.newPlot('telemetry-lap-chart', tracesLap, layoutLap, {displayModeBar: false, responsive: true});
                    bindCustomTooltip('telemetry-lap-chart', 'x', (x) => `Volta ${x}`, (val, pt) => pt.text || val);

                    Plotly.newPlot('telemetry-map-chart', [traceMap, startPoint], layoutMap, {displayModeBar: false, responsive: true});
                    window.dispatchEvent(new Event('resize'));

                    // --- CLICK HANDLER: Capturar Clique no Lap Chart ---
                    const lapChartEl = document.getElementById('telemetry-lap-chart');
                    lapChartEl.on('plotly_click', async function(eventData) {
                        const pt = eventData.points[0];
                        // Extrair nome do piloto do trace (removendo tags HTML)
                        const rawName = pt.data.name.replace(/<[^>]*>/g, '').trim();
                        const lapNum = pt.x;

                        // Evitar duplicata
                        const key = `${rawName}_L${lapNum}`;
                        if (window._selectedLaps.find(s => s.key === key)) return;

                        const driverInfo = window._driverTeamMap[rawName] || { color: '#00F0FF' };

                        // Adicionar à lista de selecionados
                        window._selectedLaps.push({ key, driver: rawName, lap: lapNum, color: driverInfo.color });

                        // Atualizar UI do painel de seleção
                        updateSelectedLapsPanel();

                        // Fetch da telemetria específica e replotar
                        await fetchAndPlotSelectedLaps();
                    });
                }, 100);

            } catch (err) {
                console.error("Telemetry Error:", err);
                loader.style.display = 'none';
                dashContainer.style.opacity = '1';
                alert("Erro ao sincronizar telemetria: " + err.message + "\nA corrida pode não dispor de rastreios públicos ainda.");
            }
        };

        // Escuta apenas a mudança de corrida caso queira recarregar os dados passivos se necessário, mas o gatilho Master é Button Cllick
        racesSelect.addEventListener('change', () => {
            // Opcional: Animação sutil de aviso de "Pronto pra Gerar" no botão
            btnGenerate.style.boxShadow = '0 0 10px rgba(0,255,0,0.5)';
            setTimeout(() => btnGenerate.style.boxShadow = 'none', 500);
        });

        // Substituindo Listener AutoLoad pelos Menus extintos pelo Click do Botão Gerar Matriz
        btnGenerate.addEventListener('click', generateMultiTelemetry);

        // Botão LIMPAR DADOS — reseta toda a visualização
        document.getElementById('btn-clear-telemetry').addEventListener('click', () => {
            // Esconder dashboard
            const dash = document.getElementById('telemetry-dash-container');
            dash.style.display = 'none';

            // Purge gráficos Plotly
            Plotly.purge('telemetry-lap-chart');
            Plotly.purge('telemetry-map-chart');
            Plotly.purge('telemetry-detail-chart');

            // Limpar KPIs
            document.getElementById('tel-kpi-row').innerHTML = '';

            // Resetar voltas selecionadas
            window._selectedLaps = [];
            const panel = document.getElementById('selected-laps-panel');
            if (panel) panel.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem;">Nenhuma volta selecionada. Clique nos pontos do Lap Chart ↑</span>';
            document.getElementById('telemetry-detail-chart').style.display = 'none';

            // Desmarcar todos os checkboxes de pilotos
            const toggles = document.getElementById('driver-toggles-container');
            if (toggles) {
                toggles.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                    cb.checked = false;
                    cb.parentElement.style.background = 'rgba(11, 20, 38, 0.6)';
                    cb.parentElement.style.borderColor = 'var(--border-color)';
                    cb.parentElement.style.color = 'var(--text-muted)';
                    cb.parentElement.style.textShadow = 'none';
                });
            }
        });

    } catch(e) { console.error(e); }
}

/**
 * [EN] Updates the selected laps panel UI with colored tags.
 * [PT-BR] Atualiza o painel visual de voltas selecionadas com tags coloridas.
 */
function updateSelectedLapsPanel() {
    const panel = document.getElementById('selected-laps-panel');
    const noMsg = document.getElementById('no-laps-msg');

    if (window._selectedLaps.length === 0) {
        panel.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem;" id="no-laps-msg">Nenhuma volta selecionada. Clique nos pontos do Lap Chart ↑</span>';
        document.getElementById('telemetry-detail-chart').style.display = 'none';
        return;
    }

    panel.innerHTML = window._selectedLaps.map(s => `
        <span class="hud-bracket" style="
            display: inline-flex; align-items: center; gap: 6px;
            padding: 4px 10px;
            background: rgba(11, 20, 38, 0.7);
            border: 1px solid ${s.color};
            color: ${s.color};
            font-family: var(--font-header);
            font-size: 0.8rem;
            cursor: default;
        ">
            ${s.driver} L${s.lap}
            <span style="cursor: pointer; font-size: 1rem; opacity: 0.7;"
                  onclick="removeLapSelection('${s.key}')"
                  onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.7'"
            >✕</span>
        </span>
    `).join('');
}

/**
 * [EN] Removes a lap from the selection and replots.
 * [PT-BR] Remove uma volta da seleção e replota o gráfico de detalhe.
 */
async function removeLapSelection(key) {
    window._selectedLaps = window._selectedLaps.filter(s => s.key !== key);
    updateSelectedLapsPanel();
    await fetchAndPlotSelectedLaps();
}

/**
 * [EN] Selects the fastest lap of a driver from the KPI card click.
 * [PT-BR] Seleciona a volta mais rápida de um piloto ao clicar no card KPI.
 */
async function selectFastestLap(driverName, lapNum, color) {
    const key = `${driverName}_L${lapNum}`;
    if (window._selectedLaps.find(s => s.key === key)) return; // evitar duplicata
    window._selectedLaps.push({ key, driver: driverName, lap: lapNum, color });
    updateSelectedLapsPanel();
    await fetchAndPlotSelectedLaps();
}

// Expose globally for inline onclick handlers
window.removeLapSelection = removeLapSelection;
window.selectFastestLap = selectFastestLap;

/**
 * [EN] Fetches telemetry for all selected laps and plots the detail chart.
 * [PT-BR] Busca a telemetria de cada volta selecionada via /telemetry/lap/
 * e plota todas sobrepostas no gráfico de Análise Detalhada.
 */
async function fetchAndPlotSelectedLaps() {
    const detailEl = document.getElementById('telemetry-detail-chart');

    if (window._selectedLaps.length === 0) {
        detailEl.style.display = 'none';
        Plotly.purge('telemetry-detail-chart');
        return;
    }

    detailEl.style.display = 'block';

    const ctx = window._telemetryContext;

    const buildTrace = (xData, yData, name, color, yaxisIdx, unit = '') => ({
        x: clampDec(xData),
        y: clampDec(yData),
        mode: 'lines',
        name: `<span style="color: ${color}">${name}</span>`,
        line: { color: color, width: 2 },
        xaxis: 'x' + (yaxisIdx === 1 ? '' : yaxisIdx),
        yaxis: 'y' + (yaxisIdx === 1 ? '' : yaxisIdx),
        showlegend: yaxisIdx === 1
    });

    const traces = [];

    // Fetch todas as voltas em paralelo
    const results = await Promise.allSettled(
        window._selectedLaps.map(async (sel) => {
            const url = `/telemetry/lap/?year=${ctx.season}&round_num=${ctx.roundNum}&session_type=${ctx.sessionType}&driver=${sel.driver}&lap_number=${sel.lap}`;
            const lapData = await fetchAPI(url);
            return { sel, lapData };
        })
    );

    results.forEach(result => {
        if (result.status !== 'fulfilled') return;
        const { sel, lapData } = result.value;
        const label = `${sel.driver} L${sel.lap}`;
        const color = sel.color;

        traces.push(
            buildTrace(lapData.telemetry.distance, lapData.telemetry.speed, label, color, 1, ' Km/h'),
            buildTrace(lapData.telemetry.distance, lapData.telemetry.throttle, label, color, 2, '%'),
            buildTrace(lapData.telemetry.distance, lapData.telemetry.brake, label, color, 3, ''),
            buildTrace(lapData.telemetry.distance, lapData.telemetry.rpm, label, color, 4, ' RPM'),
            buildTrace(lapData.telemetry.distance, lapData.telemetry.gear, label, color, 5, 'ª Marcha')
        );
    });

    const axisDefaults = {
        gridcolor: '#1A2C42',
        showspikes: true,
        spikemode: 'across',
        spikesnap: 'cursor',
        showline: true,
        spikecolor: 'rgba(0, 240, 255, 0.15)',
        spikethickness: 1,
        spikedash: 'dash'
    };

    const layoutDetail = {
        height: 1200,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#8AA4C8', family: 'Orbitron' },
        margin: { t: 40, b: 40, l: 60, r: 20 },
        grid: { rows: 5, columns: 1, pattern: 'independent', roworder: 'top to bottom' },
        legend: { orientation: 'h', y: 1.05, x: 0 },
        autosize: true,
        xaxis:  { title: 'Distância (m)', ...axisDefaults },
        xaxis2: { matches: 'x', showticklabels: false, ...axisDefaults },
        xaxis3: { matches: 'x', showticklabels: false, ...axisDefaults },
        xaxis4: { matches: 'x', showticklabels: false, ...axisDefaults },
        xaxis5: { matches: 'x', showticklabels: false, ...axisDefaults },
        yaxis:  { title: 'Km/h', gridcolor: '#1A2C42', automargin: true },
        yaxis2: { title: 'Acel %', gridcolor: '#1A2C42', range: [-5, 105], automargin: true },
        yaxis3: { title: 'Freio (0-1)', gridcolor: '#1A2C42', tickvals: [0, 1], range: [-0.2, 1.2], automargin: true },
        yaxis4: { title: 'RPM', gridcolor: '#1A2C42', automargin: true },
        yaxis5: { title: 'Marcha', gridcolor: '#1A2C42', tickvals: [1,2,3,4,5,6,7,8], automargin: true }
    };

    Plotly.purge('telemetry-detail-chart');
    Plotly.newPlot('telemetry-detail-chart', traces, layoutDetail, { displayModeBar: false, responsive: true });
    bindCustomTooltip('telemetry-detail-chart', 'x', (x) => `Distância: ${x}m`, (val, pt) => {
        switch(pt.data.yaxis) {
            case 'y': return val + ' Km/h';
            case 'y2': return val + '%';
            case 'y3': return val + '';
            case 'y4': return val + ' RPM';
            case 'y5': return val + 'ª Marcha';
            default: return val;
        }
    });

    window.dispatchEvent(new Event('resize'));
}

// 3. Evolution Controller
async function loadEvolution(season) {
    try {
        const typeSelect = document.getElementById('evolution-type');
        const titleEl = document.getElementById('evolution-title');

        const races = await fetchAPI(`/races/?season=${season}&limit=100`);
        races.sort((a,b) => a.round - b.round);
        const raceIds = races.map(r => r.id);
        const raceNames = races.map(r => `R${r.round}`);

        // Buscar resultados do ano construindo o gráfico por corrida para respeitar o limite de 500 registros por query da API
        let allResults = [];
        for (let rid of raceIds) {
            const raceRes = await fetchAPI(`/results/?race_id=${rid}&limit=500`);
            allResults = allResults.concat(raceRes);
        }

        const renderChart = async () => {
            const isDrivers = typeSelect.value === 'drivers';
            titleEl.textContent = isDrivers ? 'Evolução do Campeonato (Pilotos)' : 'Evolução do Campeonato (Construtores)';
            const traces = [];

            if (!isDrivers) {
                const constructors = await fetchAPI(`/standings/constructors/?season=${season}`);
                for (let c of constructors) {
                    const teamName = c.constructor_name; // ja vem no standing enriquecido

                    let cumulative = 0;
                    const yData = raceIds.map(rid => {
                        const teamResults = allResults.filter(res => res.race_id === rid && res.constructor_id === c.constructor_id);
                        const racePoints = teamResults.reduce((sum, res) => sum + (res.points || 0), 0);
                        cumulative += racePoints;
                        return cumulative;
                    });

                    traces.push({
                        x: raceNames,
                        y: yData,
                        mode: 'lines+markers',
                        name: `<span style="color: ${getTeamColor(teamName)}">${escapeHTML(teamName)}</span>`,
                        line: { shape: 'spline', color: getTeamColor(teamName), width: 3 },
                        marker: { size: 6 }
                    });
                }
            } else {
                const driversStd = await fetchAPI(`/standings/drivers/?season=${season}`);
                const topDrivers = driversStd; // Carrega TODOS os drivers conforme solicitação

                for (let d of topDrivers) {
                    const permNum = d.permanent_number ? ` - ${d.permanent_number}` : '';
                    const driverName = `${d.driver_name}${permNum}`; // ja vem no standing enriquecido

                    // Guardamos também na variável loop temporária para ordenar tudo por A-Z mais tarde
                    d.fullName = driverName;
                    const dRes = allResults.find(res => res.driver_id === d.driver_id);
                    // constructor_name ja vem no result enriquecido
                    const teamColor = dRes ? getTeamColor(dRes.constructor_name) : '#ccc';

                    let cumulative = 0;
                    const yData = raceIds.map(rid => {
                        const drvResult = allResults.find(res => res.race_id === rid && res.driver_id === d.driver_id);
                        cumulative += drvResult ? (drvResult.points || 0) : 0;
                        return cumulative;
                    });

                    traces.push({
                        x: raceNames,
                        y: yData,
                        mode: 'lines+markers',
                        name: `<span style="color: ${teamColor}">${escapeHTML(driverName)}</span>`,
                        line: { shape: 'spline', color: teamColor, width: 3 },
                        marker: { size: 6 }
                    });
                }

                traces.sort((a,b) => a.name.localeCompare(b.name));
            }

            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#8AA4C8', family: 'Orbitron' },
                xaxis: {
                    tickangle: -45, // Rotaciona as legendas de Rounds para não sobreporem
                    gridcolor: '#1A2C42',
                    tickmode: 'linear', // Força espaçamento rígido para todos aparecerem iguais
                    dtick: 1,           // Mostra os labels de 1 em 1 para garantir o mesmo peso
                    tickfont: { size: 10 }, // Reduz sutilmente o R1, R2 para melhor fit global
                    showspikes: true,
                    spikemode: 'across',
                    spikesnap: 'cursor',
                    showline: true,
                    spikecolor: 'rgba(0, 240, 255, 0.15)',
                    spikethickness: 1,
                    spikedash: 'dash'
                },
                yaxis: { title: 'Pontos Acumulados', gridcolor: '#1A2C42' },
                margin: { t: 40, b: 60, l: 80, r: 20 }, // Margem L expandida para isolar label y dos dígitos
                legend: {
                    orientation: 'h',
                    y: 1.15,        // Um pouco mais acima para evitar sobrepor o gráfico
                    x: 0,           // Alinhado a esquerda
                    bgcolor: 'rgba(0,0,0,0)',
                    bordercolor: 'rgba(0,0,0,0)',
                    font: { size: 9 },      // Reduz a fonte ainda mais (ideal para nomes longos)
                    itemwidth: 45           // Força uma distância de respiro maior entre os itens
                }
            };

            Plotly.newPlot('evolution-chart', traces, layout, {displayModeBar: false, responsive: true});
            bindCustomTooltip('evolution-chart', 'x', (x) => x, (val) => val + ' pts');
        };

        await renderChart();

        // Aciona evento de recálculo apenas para este request via Dropdown
        typeSelect.onchange = renderChart;

    } catch(e) { console.error(e); }
}

// 4. Head-to-Head Controller
async function loadH2H(season) {
    try {
        const drivers = await fetchAPI(`/standings/drivers/?season=${season}`);

        // Setup dropdowns
        const d1Select = document.getElementById('h2h-driver1');
        const d2Select = document.getElementById('h2h-driver2');

        // Only populate if empty or season changed
        d1Select.innerHTML = '<option value="" disabled selected>Piloto 1</option>';
        d2Select.innerHTML = '<option value="" disabled selected>Piloto 2</option>';

        // Coletar dados detalhados para exibição textual (Nome + Número)
        const driverOptions = drivers.map((row) => {
            const permNum = row.permanent_number ? ` - ${row.permanent_number}` : '';
            return {
                id: row.driver_id,
                name: escapeHTML(`${row.driver_name}${permNum}`) // ja vem no standing enriquecido
            };
        });

        // Ordernar alfabeticamente o dropdown
        driverOptions.sort((a, b) => a.name.localeCompare(b.name));

        for (let opt of driverOptions) {
            d1Select.insertAdjacentHTML('beforeend', `<option value="${opt.id}">${opt.name}</option>`);
            d2Select.insertAdjacentHTML('beforeend', `<option value="${opt.id}">${opt.name}</option>`);
        }

        const metricSelect = document.getElementById('h2h-metric');

        const renderH2HChart = async () => {
            const d1 = d1Select.value;
            const d2 = d2Select.value;
            if(!d1 || !d2) return;

            const [res1, res2] = await Promise.all([
                fetchAPI(`/results/?season=${season}&driver_id=${d1}&limit=500`),
                fetchAPI(`/results/?season=${season}&driver_id=${d2}&limit=500`)
            ]);

            const races = await fetchAPI(`/races/?season=${season}&limit=100`);
            races.sort((a,b) => a.round - b.round);
            const raceNames = races.map(r => `R${r.round}`);
            const raceIds = races.map(r => r.id);

            const isPoints = metricSelect.value === 'points';

            const getDriverDataList = (resultsList) => {
                let cumulative = 0;
                return raceIds.map(rid => {
                    const r = resultsList.find(x => x.race_id === rid);
                    if (isPoints) {
                        if(r) cumulative += r.points;
                        return cumulative;
                    } else {
                        return r && r.position ? r.position : null;
                    }
                });
            };

            const teamColorForDriver = (resultsList) => {
                // constructor_name ja vem no result enriquecido
                const firstValidResult = resultsList.find(r => r.constructor_name);
                return firstValidResult ? getTeamColor(firstValidResult.constructor_name) : '#ccc';
            };

            const color1 = teamColorForDriver(res1);
            const color2 = teamColorForDriver(res2);

            const n1 = d1Select.options[d1Select.selectedIndex].text;
            const n2 = d2Select.options[d2Select.selectedIndex].text;

            const trace1 = {
                x: raceNames,
                y: getDriverDataList(res1),
                mode: 'lines+markers',
                name: `<span style="color: ${color1}">${n1}</span>`,
                line: { shape: 'spline', color: color1, width: 3 },
                marker: { size: 6 }
            };

            const trace2 = {
                x: raceNames,
                y: getDriverDataList(res2),
                mode: 'lines+markers',
                name: `<span style="color: ${color2}">${n2}</span>`,
                line: { shape: 'spline', color: color2, width: 3 },
                marker: { size: 6 }
            };

            // Ajusta o Layout (inverte eixo Y se for Posição)
            const yAxisLayout = {
                title: isPoints ? 'Pontos Acumulados' : 'Posição de Chegada',
                gridcolor: '#1A2C42'
            };
            if (!isPoints) yAxisLayout.autorange = 'reversed';

            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#8AA4C8', family: 'Orbitron' },
                xaxis: {
                    tickangle: -45, // Rotaciona as legendas de Rounds para não sobreporem
                    gridcolor: '#1A2C42',
                    tickmode: 'linear', // Força espaçamento rígido para todos aparecerem iguais
                    dtick: 1,           // Mostra os labels de 1 em 1 para garantir o mesmo peso
                    tickfont: { size: 10 }, // Reduz sutilmente o R1, R2 para melhor fit global
                    showspikes: true,
                    spikemode: 'across',
                    spikesnap: 'cursor',
                    showline: true,
                    spikecolor: 'rgba(0, 240, 255, 0.15)',
                    spikethickness: 1,
                    spikedash: 'dash'
                },
                yaxis: yAxisLayout,
                margin: { t: 40, b: 60, l: 80, r: 20 },
                legend: {
                    orientation: 'h',
                    y: 1.15,
                    x: 0,
                    bgcolor: 'rgba(0,0,0,0)',
                    bordercolor: 'rgba(0,0,0,0)',
                    font: { size: 9 },      // Reduz a fonte ainda mais (ideal para nomes longos)
                    itemwidth: 45           // Força uma distância de respiro maior entre os itens
                }
            };

            document.getElementById('h2h-chart-title').textContent = isPoints ? 'Evolução de Pontos (Corrida a Corrida)' : 'Posições (Corrida a Corrida)';
            Plotly.newPlot('h2h-chart', [trace1, trace2], layout, {displayModeBar: false, responsive: true});
            bindCustomTooltip('h2h-chart', 'x', (x) => x, (val) => isPoints ? val + ' pts' : val + 'º');

            // 2) Calculating Stats — calcStats importado de ./lib/stats.js

            const s1 = calcStats(res1);
            const s2 = calcStats(res2);

            // Populate Panel
            document.getElementById('h2h-stats-panel').style.display = 'grid'; // Mostrar grid

            document.getElementById('s-pts-1').textContent = s1.pts;
            document.getElementById('s-pts-2').textContent = s2.pts;
            document.getElementById('s-win-1').textContent = s1.wins;
            document.getElementById('s-win-2').textContent = s2.wins;
            document.getElementById('s-pod-1').textContent = s1.pods;
            document.getElementById('s-pod-2').textContent = s2.pods;
            document.getElementById('s-dnf-1').textContent = s1.dnfs;
            document.getElementById('s-dnf-2').textContent = s2.dnfs;
            document.getElementById('s-avg-1').textContent = s1.avgPos;
            document.getElementById('s-avg-2').textContent = s2.avgPos;
            document.getElementById('s-races-1').textContent = s1.racesD;
            document.getElementById('s-races-2').textContent = s2.racesD;

            // Cores Atribuidas aos Valores dos Stats
            document.querySelectorAll('.s-val-1').forEach(el => el.style.color = color1);
            document.querySelectorAll('.s-val-2').forEach(el => el.style.color = color2);

            // 3) Radar Chart Area
            // Normalizar entre 0 a 100 para comparar numeros de escalas diferentes no Radar
            const maxPts = Math.max(s1.pts, s2.pts, 1);
            const maxWins = Math.max(s1.wins, s2.wins, 1);
            const maxPods = Math.max(s1.pods, s2.pods, 1);
            // AVG pos invertido no max (Pos1 melhor que Pos20)
            const maxAvgP = 20;

            // Para DNFs o menor DNF é melhor, por isso invertemos a pontuação
            // Menor DNF possível é 0 = 100%. Maior DNF possível de ambos perde score.

            const r1Vals = [
                (s1.pts / maxPts) * 100,
                (s1.wins / maxWins) * 100,
                (s1.pods / maxPods) * 100,
                100 - (s1.dnfs * 5), // Regra empírica suave
                ((maxAvgP - parseFloat(s1.avgPos)) / maxAvgP) * 100,
                (s1.racesD / Math.max(s1.racesD, s2.racesD, 1)) * 100
            ];
            r1Vals.push(r1Vals[0]); // Fechar o polígono

            const r2Vals = [
                (s2.pts / maxPts) * 100,
                (s2.wins / maxWins) * 100,
                (s2.pods / maxPods) * 100,
                100 - (s2.dnfs * 5),
                ((maxAvgP - parseFloat(s2.avgPos)) / maxAvgP) * 100,
                (s2.racesD / Math.max(s1.racesD, s2.racesD, 1)) * 100
            ];
            r2Vals.push(r2Vals[0]);

            const fields = ['Pontos', 'Vitórias', 'Pódios', 'Terminou/Consistência', 'Avg Posição', 'GPs', 'Pontos'];

            const dataRadar = [
              {
                type: 'scatterpolar',
                r: r1Vals,
                theta: fields,
                fill: 'toself',
                name: `<span style="color: ${color1}">${n1}</span>`,
                line: { color: color1 },
                fillcolor: color1 + '33' // 20% opacity hexa
              },
              {
                type: 'scatterpolar',
                r: r2Vals,
                theta: fields,
                fill: 'toself',
                name: `<span style="color: ${color2}">${n2}</span>`,
                line: { color: color2 },
                fillcolor: color2 + '33'
              }
            ];

            const layoutRadar = {
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              font: { color: '#8AA4C8', family: 'Orbitron' },
              hovermode: 'x unified', // Força com que o mouse dispare evento sobre o eixo Angular inteiro (pegando os 2 pilotos)
              polar: {
                radialaxis: { visible: false, range: [0, 100] },
                angularaxis: { tickfont: { size: 10, color: '#00F0FF' } },
                bgcolor: 'rgba(0,0,0,0)'
              },
              margin: { t: 40, b: 40, l: 40, r: 40 },
              legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' }
            };

            Plotly.newPlot('h2h-radar', dataRadar, layoutRadar, {displayModeBar: false, responsive: true});
            bindCustomTooltip('h2h-radar', 'theta', (x) => `Performance ${x}`, (val) => Number(val).toFixed(1) + '%');
        };

        d1Select.onchange = renderH2HChart;
        d2Select.onchange = renderH2HChart;
        metricSelect.onchange = renderH2HChart;

    } catch(e) { console.error(e); }
}

// 5. Pit Stops Controller
async function loadPits(season) {
    try {
        const racesSelect = document.getElementById('pits-race');
        racesSelect.innerHTML = '<option disabled>Carregando...</option>';

        const races = await fetchAPI(`/races/?season=${season}&limit=100`);
        if (races.length === 0) {
            racesSelect.innerHTML = '<option disabled>Sem Corridas</option>';
            return;
        }

        races.sort((a,b) => a.round - b.round);
        racesSelect.innerHTML = '';
        races.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.textContent = `R${r.round} - ${r.race_name || 'Corrida'}`;
            racesSelect.appendChild(opt);
        });

        const renderPitCharts = async () => {
            const raceId = racesSelect.value;
            if(!raceId) return;

            const [pitsData, resultsData, driversSt] = await Promise.all([
                fetchAPI(`/pitstops/?race_id=${raceId}&limit=500`),
                fetchAPI(`/results/?race_id=${raceId}&limit=100`),
                fetchAPI(`/standings/drivers/?season=${season}`)
            ]);

            if(!pitsData || pitsData.length === 0) {
                document.getElementById('pits-duration-chart').innerHTML = '<p style="color:#CFCFCF; padding:20px;">Nenhum pit stop registrado.</p>';
                document.getElementById('pits-strategy-chart').innerHTML = '';
                document.getElementById('pits-dist-chart').innerHTML = '';
                return;
            }

            // Build Drivers Info Lookup a partir dos results enriquecidos (nome + equipe inline)
            const driverMap = {}; // driver_id -> { name, team }
            for (let res of resultsData) {
                if (!driverMap[res.driver_id]) {
                    driverMap[res.driver_id] = {
                        name: escapeHTML(res.driver_name || 'Desconhecido'),
                        team: res.constructor_name || 'Desconhecido'
                    };
                }
            }

            // Unique drivers from pits
            const pitDriversIds = [...new Set(pitsData.map(p => p.driver_id))];

            // Fallback para pilotos presentes nos pits mas ausentes nos resultados
            pitDriversIds.forEach((did) => {
                if (!driverMap[did]) {
                    driverMap[did] = { name: `Piloto ${did}`, team: 'Desconhecido' };
                }
            });

            // Structure data for Plotly
            let driverStats = [];
            // driverStats will store: { name, team, avgDuration, numStops, durations: [] }

            for (let did of pitDriversIds) {
                const driverPits = pitsData.filter(p => p.driver_id === did);
                let validSecs = [];
                driverPits.forEach(p => {
                    let sec = 0;
                    if(p.milliseconds) sec = p.milliseconds / 1000.0;
                    else if(p.duration) sec = parseFloat(p.duration);
                    if(sec && sec > 0) validSecs.push(sec);
                });

                if(validSecs.length > 0) {
                    const avg = validSecs.reduce((a,b)=>a+b, 0) / validSecs.length;
                    driverStats.push({
                        name: driverMap[did].name,
                        team: driverMap[did].team,
                        avgDuration: avg,
                        numStops: validSecs.length,
                        durations: validSecs
                    });
                }
            }

            // --- CHART 1: Duração Média (Horizontal Bar) ---
            // Ordenar por Duração DESC para o BarChart Horizontal colocar os mais lentos embaixo e rápidos em cima (usando reversed)
            let durationStats = [...driverStats].sort((a,b) => a.avgDuration - b.avgDuration);

            const maxDur = Math.max(...durationStats.map(d => d.avgDuration));
            const traceDuration = {
                x: durationStats.map(d => d.avgDuration),
                y: durationStats.map(d => d.name),
                type: 'bar',
                orientation: 'h',
                name: 'Duração Média',
                text: durationStats.map(d => d.avgDuration.toFixed(2) + 's'),
                textposition: 'outside',
                cliponaxis: false,
                marker: { color: durationStats.map(d => getTeamColor(d.team)) }
            };

            const layoutDuration = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#8AA4C8', family: 'Orbitron' },
                margin: { t: 20, b: 40, l: 10, r: 40 },
                xaxis: {
                    title: 'Segundos', gridcolor: '#1A2C42',
                    range: [0, maxDur * 1.20]
                },
                yaxis: {
                    autorange: 'reversed',
                    automargin: true,
                    ticksuffix: '      ',
                    ticklabelposition: "outside left"
                }
            };
            Plotly.newPlot('pits-duration-chart', [traceDuration], layoutDuration, {displayModeBar: false, responsive: true});
            bindCustomTooltip('pits-duration-chart', 'y', (y) => y, (val) => val);


            // --- CHART 2: Paradas por Piloto (Horizontal Bar) ---
            // Ordenamos por número de paradas
            let stopsStats = [...driverStats].sort((a,b) => a.numStops - b.numStops);

            const maxStops = Math.max(...stopsStats.map(d => d.numStops));
            const traceStops = {
                x: stopsStats.map(d => d.numStops),
                y: stopsStats.map(d => d.name),
                type: 'bar',
                orientation: 'h',
                name: 'Total de Paradas',
                text: stopsStats.map(d => d.numStops),
                textposition: 'outside',
                cliponaxis: false,
                marker: { color: stopsStats.map(d => getTeamColor(d.team)) }
            };

            const layoutStops = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#8AA4C8', family: 'Orbitron' },
                margin: { t: 20, b: 40, l: 10, r: 40 },
                xaxis: {
                    title: 'Qtd. de Pit Stops', gridcolor: '#1A2C42',
                    range: [0, maxStops + 1]
                },
                yaxis: {
                    autorange: 'reversed',
                    automargin: true,
                    ticksuffix: '      ',
                    ticklabelposition: "outside left"
                }
            };
            Plotly.newPlot('pits-strategy-chart', [traceStops], layoutStops, {displayModeBar: false, responsive: true});
            bindCustomTooltip('pits-strategy-chart', 'y', (y) => y, (val) => val + ' stops');


            // --- CHART 3: Distribuição por Equipe (BoxPlot) ---
            // Agrupar equipes exclusivas
            const uniqueTeams = [...new Set(driverStats.map(d => d.team))];
            uniqueTeams.sort((a, b) => a.localeCompare(b)); // Teams em Ordem Alfabética

            const boxTraces = uniqueTeams.map(teamName => {
                const teamDurations = [];
                driverStats.filter(d => d.team === teamName).forEach(d => {
                    teamDurations.push(...d.durations);
                });

                return {
                    y: teamDurations,
                    type: 'box',
                    name: escapeHTML(teamName),
                    boxpoints: 'all',          // mostra todos os pontos scatter
                    jitter: 0.3,
                    pointpos: -1.8,
                    marker: { color: getTeamColor(teamName) },
                    line: { width: 2 }
                };
            });

            const layoutBox = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#8AA4C8', family: 'Orbitron' },
                margin: { t: 20, b: 60, l: 60, r: 20 },
                xaxis: { title: 'Equipe' },
                yaxis: { title: 'Duração (s)', gridcolor: '#1A2C42' },
                showlegend: false
            };
            Plotly.newPlot('pits-dist-chart', boxTraces, layoutBox, {displayModeBar: false, responsive: true});
            bindCustomTooltip('pits-dist-chart', 'x', (x) => `Equipe: ${x}`, (val) => Number(val).toFixed(2) + 's');
        };

        // Escutar Mudança no Dropdown
        racesSelect.onchange = renderPitCharts;
        // Desenhar inicialmente
        await renderPitCharts();

    } catch(e) { console.error(e); }
}

// 6. Grid Analysis Controller
async function loadGrid(season) {
    try {
        const racesSelect = document.getElementById('grid-race');
        racesSelect.innerHTML = '<option disabled>Carregando...</option>';

        // Fetch basic data for translations and overall season metrics
        const races = await fetchAPI(`/races/?season=${season}&limit=100`);

        if (races.length === 0) {
            racesSelect.innerHTML = '<option disabled>Sem Corridas</option>';
            return;
        }

        races.sort((a,b) => a.round - b.round);
        racesSelect.innerHTML = '';
        races.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.textContent = `R${r.round} - ${r.race_name || 'Corrida'}`;
            racesSelect.appendChild(opt);
        });

        // KPI: Global Pole Conversion (Asynchronous to prevent UI blocking)
        document.getElementById('grid-pole-conversion').textContent = `...`;
        (async () => {
            try {
                const resultsPromises = races.map(r => fetchAPI(`/results/?race_id=${r.id}&limit=100`));
                const resultsArray = await Promise.all(resultsPromises);
                const allSeasonResults = resultsArray.flat();

                const poleSits = allSeasonResults.filter(r => parseInt(r.grid) === 1);
                const poleWins = poleSits.filter(r => parseInt(r.position) === 1);
                const poleConvPct = poleSits.length > 0 ? ((poleWins.length / poleSits.length) * 100).toFixed(1) : 0;
                document.getElementById('grid-pole-conversion').textContent = `${poleConvPct}%`;
            } catch(e) {
                document.getElementById('grid-pole-conversion').textContent = `N/A`;
            }
        })();

        const renderGridCharts = async () => {
            const raceId = racesSelect.value;
            if(!raceId) return;

            // Fetch specific grid-finish match for the dropdown race
            const results = await fetchAPI(`/results/?race_id=${raceId}&limit=100`);

            let valid = results.filter(r => parseInt(r.grid) > 0 && parseInt(r.position) > 0);

            // Nome do piloto e equipe ja vem no result enriquecido -> sem N+1
            let chartData = valid.map(r => {
                const driverName = r.driver_name || 'Desconhecido';
                const teamName = r.constructor_name || 'N/A';

                return {
                    driverName: driverName,
                    shortName: driverName.split(' ').pop(),
                    teamColor: getTeamColor(teamName),
                    grid: parseInt(r.grid),
                    position: parseInt(r.position),
                    gained: parseInt(r.grid) - parseInt(r.position)
                };
            });

            if(chartData.length === 0) return;

            // --- CHART 1: Scatter (Grid vs Finish) ---
            const maxPos = Math.max(...chartData.map(d => Math.max(d.grid, d.position))) + 1;

            const scatterTraces = chartData.map(d => ({
                x: [d.grid],
                y: [d.position],
                mode: 'markers+text',
                marker: { size: 12, color: d.teamColor, line: {width: 1, color: '#FFF'} },
                text: [d.shortName],
                textposition: 'top center',
                textfont: {size: 10, color: '#E8E8E8'},
                name: d.driverName,
                showlegend: false
            }));

            // Dashboard Math line
            scatterTraces.push({
                x: [1, maxPos],
                y: [1, maxPos],
                mode: 'lines',
                line: {dash: 'dash', color: 'rgba(255,255,255,0.2)'},
                hoverinfo: 'none',
                showlegend: false
            });

            const layoutScatter = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#8AA4C8', family: 'Orbitron' },
                margin: { t: 20, b: 40, l: 40, r: 20 },
                xaxis: {
                    title: 'Grid',
                    gridcolor: '#1A2C42',
                    showspikes: true,
                    spikemode: 'across',
                    spikesnap: 'cursor',
                    showline: true,
                    spikecolor: 'rgba(0, 240, 255, 0.15)',
                    spikethickness: 1,
                    spikedash: 'dash'
                },
                yaxis: { title: 'Chegada', gridcolor: '#1A2C42', autorange: 'reversed' },
                height: 550
            };
            Plotly.newPlot('grid-scatter-chart', scatterTraces, layoutScatter, {displayModeBar: false, responsive: true});
            bindCustomTooltip('grid-scatter-chart', 'x', (x) => `Grid Posição: ${x}º`, (val, pt) => `Chegada em ${pt.y}º`);

            // --- CHART 2: BarChart (Positions Math Gained/Lost) ---
            chartData.sort((a,b) => a.gained - b.gained);

            const borderColors = chartData.map(d => {
                if (d.gained > 0) return '#00FFD1';
                else if (d.gained < 0) return '#FF2E4C';
                else return '#6B7B8D';
            });

            const texts = chartData.map(d => d.gained > 0 ? `+${d.gained}` : `${d.gained}`);

            const traceGained = {
                x: chartData.map(d => d.gained),
                y: chartData.map(d => d.driverName),
                type: 'bar',
                orientation: 'h',
                marker: {
                    color: chartData.map(d => d.teamColor),
                    line: { color: borderColors, width: 2 }
                },
                text: texts,
                textposition: 'outside',
                cliponaxis: false
            };

            const layoutGained = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#8AA4C8', family: 'Orbitron' },
                margin: { t: 20, b: 40, l: 150, r: 20 },
                xaxis: { title: 'Posições', gridcolor: '#1A2C42' },
                yaxis: { title: '', automargin: true },
                height: 550
            };
            Plotly.newPlot('grid-gained-chart', [traceGained], layoutGained, {displayModeBar: false, responsive: true});
            bindCustomTooltip('grid-gained-chart', 'y', (y) => y, (val, pt) => {
                const pos = Number(pt.x);
                return (pos > 0 ? '+' : '') + pos + ' posições';
            });
        };

        racesSelect.onchange = renderGridCharts;
        await renderGridCharts();

    } catch(e) { console.error(e); }
}

// 7. History Controller
async function loadHistory(season) {
    try {
        // Reset inputs
        document.getElementById('history-total-races').textContent = '...';
        document.getElementById('history-champion-name').textContent = '...';
        document.getElementById('history-champion-points').textContent = '...';
        document.getElementById('history-calendar-table').querySelector('tbody').innerHTML = '';
        document.getElementById('history-standings-table').querySelector('tbody').innerHTML = '';
        const racesSelect = document.getElementById('history-race-select');
        racesSelect.innerHTML = '<option value="" disabled selected>Carregando...</option>';

        // Fetch basic data
        const [races, drv_standings] = await Promise.all([
            fetchAPI(`/races/?season=${season}&limit=100`),
            fetchAPI(`/standings/drivers/?season=${season}`)
        ]);

        if (races.length === 0) {
            document.getElementById('history-total-races').textContent = '0';
            racesSelect.innerHTML = '<option disabled>Sem Corridas</option>';
            return;
        }

        // --- KPIs ---
        document.getElementById('history-total-races').textContent = races.length;

        let championData = null;
        if (drv_standings.length > 0) {
            drv_standings.sort((a,b) => a.position - b.position);
            championData = drv_standings[0];
            // driver_name ja vem no standing enriquecido
            document.getElementById('history-champion-name').textContent = escapeHTML(championData.driver_name || '');
            document.getElementById('history-champion-points').textContent = `${championData.points} pts`;
        } else {
            document.getElementById('history-champion-name').textContent = "N/A";
            document.getElementById('history-champion-points').textContent = "0 pts";
        }

        // --- Calendar Table ---
        races.sort((a,b) => a.round - b.round);
        const calTbody = document.getElementById('history-calendar-table').querySelector('tbody');

        racesSelect.innerHTML = '<option value="" disabled>Selecione a Corrida...</option>';
        races.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${r.round}</td>
                <td>${escapeHTML(r.race_name || 'N/A')}</td>
                <td>${r.date ? r.date.substring(0,10) : ''}</td>
            `;
            calTbody.appendChild(tr);

            const opt = document.createElement('option');
            opt.value = r.id;
            opt.textContent = `R${r.round} - ${r.race_name || 'Corrida'}`;
            racesSelect.appendChild(opt);
        });

        // Auto-select last race
        if (races.length > 0) {
            racesSelect.value = races[races.length - 1].id;
        }

        // --- Final Standings Table ---
        if (drv_standings.length > 0) {
            const stdTbody = document.getElementById('history-standings-table').querySelector('tbody');

            // driver_name ja vem no standing enriquecido -> sem N+1
            drv_standings.forEach(s => {
                const driverName = s.driver_name || 'Desconhecido';
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${s.position}</td>
                    <td>${escapeHTML(driverName)}</td>
                    <td>${s.points}</td>
                    <td>${s.wins}</td>
                `;
                stdTbody.appendChild(tr);
            });
        }

        // --- Results & Podium Render Logic ---
        const renderRaceResults = async () => {
            const raceId = racesSelect.value;
            if(!raceId) return;

            const resTbody = document.getElementById('history-results-table').querySelector('tbody');
            resTbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Carregando resultados...</td></tr>';
            const podiumContainer = document.getElementById('history-podium-container');
            podiumContainer.innerHTML = '';

            const results = await fetchAPI(`/results/?race_id=${raceId}&limit=100`);

            if (!results || results.length === 0) {
                resTbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">Nenhum resultado registrado.</td></tr>';
                return;
            }

            // driver_name e constructor_name ja vem no result enriquecido -> sem N+1
            results.sort((a,b) => {
                const aPos = parseInt(a.position) || 999;
                const bPos = parseInt(b.position) || 999;
                return aPos - bPos;
            });

            resTbody.innerHTML = '';

            // Build Podium
            const top3 = results.slice(0, 3);
            const medals = ['P1', 'P2', 'P3'];
            const podiumColors = ['var(--accent-cyan)', '#C0C0C0', '#CD7F32'];

            top3.forEach((r, idx) => {
                const dName = r.driver_name || 'N/A';
                const cName = r.constructor_name || 'N/A';
                const teamColor = getTeamColor(cName);

                const card = document.createElement('div');
                card.className = 'glass-panel hud-bracket';
                card.style.flex = '1';
                card.style.padding = '15px';
                card.style.borderTop = `3px solid ${teamColor}`;

                card.innerHTML = `
                    <h3 style="color: ${podiumColors[idx]}; font-size: 1.2rem; margin-top:0;">${medals[idx]}</h3>
                    <div style="font-size: 1.1rem; font-weight: bold; margin-bottom: 5px;">${escapeHTML(dName)}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">${escapeHTML(cName)}</div>
                `;
                podiumContainer.appendChild(card);
            });

            // Build Results Table
            results.forEach(r => {
                const dName = r.driver_name || 'N/A';
                const cName = r.constructor_name || 'N/A';

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${escapeHTML(r.position_text || r.position || '-')}</td>
                    <td>${escapeHTML(dName)}</td>
                    <td>${escapeHTML(cName)}</td>
                    <td>${escapeHTML(r.grid)}</td>
                    <td>${escapeHTML(r.points)}</td>
                    <td>${escapeHTML(r.laps)}</td>
                    <td>${escapeHTML(r.status)}</td>
                `;
                resTbody.appendChild(tr);
            });
        };

        racesSelect.onchange = renderRaceResults;
        await renderRaceResults();

    } catch(e) { console.error(e); }
}
