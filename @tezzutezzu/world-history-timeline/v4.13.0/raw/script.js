function getTooltipContent(d) {
  return `
          <b>${d.civilization}</b>
          <br/>
          <b style="color:${d.color.darker()}">${d.region}</b>
          <br/>
          ${formatDate(d.start)} - ${formatDate(d.end)}
      `;
}

function createTooltip(el) {
  el.style("position", "absolute")
    .style("pointer-events", "none")
    .style("top", 0)
    .style("opacity", 0)
    .style("background", "white")
    .style("border-radius", "5px")
    .style("box-shadow", "0 0 10px rgba(0,0,0,.25)")
    .style("padding", "10px")
    .style("line-height", "1.3")
    .style("font", "11px sans-serif");
}

function getRect(d) {
  const el = d3.select(this);
  const sx = xPositionScale(d.start);
  const w = xPositionScale(d.end) - xPositionScale(d.start);
  const isLabelRight = sx > width / 2 ? sx + w < width : sx - w > 0;

  el.style("cursor", "pointer");

  el.append("rect")
    .attr("x", sx)
    .attr("height", yPositionScale.bandwidth())
    .attr("width", w)
    .attr("fill", d.color);

  el.append("text")
    .text(d.civilization)
    .attr("class", "civ-text")
    .attr("x", isLabelRight ? sx - 5 : sx + w + 5)
    .attr("y", 2.5)
    .attr("fill", "black")
    .style("text-anchor", isLabelRight ? "end" : "start")
    .style("dominant-baseline", "hanging");
}

const margin = { top: 30, right: 30, bottom: 30, left: 30 };
const height = 1000 - margin.top - margin.bottom;
const width = 1000 - margin.left - margin.right;

var svg = d3
  .select("#chart")
  .append("svg")
  .attr("width", width + margin.left + margin.right)
  .attr("height", height + margin.top + margin.bottom)
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

const yPositionScale = d3.scaleBand().range([0, height]).padding(0.2);

const xPositionScale = d3.scaleLinear().range([0, width]);

const colorScale = d3.scaleOrdinal(d3.schemeSet2);
const formatDate = (d) => (d < 0 ? `${-d}BC` : `${d}AD`);

const axisBottom = d3
  .axisBottom(xPositionScale)
  .tickPadding(2)
  .tickFormat(formatDate);

const axisTop = d3
  .axisTop(xPositionScale)
  .tickPadding(2)
  .tickFormat(formatDate);

d3.csv("civilization timelines - civilization timelines.csv", function (d) {
  return {
    ...d,
    start: +d.start,
    end: +d.end,
  };
}).then(ready);

function ready(datapoints) {
  datapoints = datapoints.sort((a, b) => a.start - b.start);

  xPositionScale.domain([
    d3.min(datapoints, (d) => d.start),
    d3.max(datapoints, (d) => d.end),
  ]);

  yPositionScale.domain(d3.range(datapoints.length));

  const dataByTimeline = d3
    .nest()
    .key((d) => d.timeline)
    .entries(datapoints);

  const dataByRegion = d3
    .nest()
    .key((d) => d.region)
    .entries(datapoints);
  
  const regions = d3
    .nest()
    .key((d) => d.region)
    .entries(datapoints)
    .map((d) => d.key);

  colorScale.domain(regions);

  const timelines = dataByTimeline.map((d) => d.key);

  let filteredData;
  filteredData = [].concat.apply(
    [],
    dataByRegion.map((d) => d.values)
  );
  console.log(dataByRegion.map((d) => d.values))
  console.log(filteredData)

  filteredData.forEach((d) => (d.color = d3.color(colorScale(d.region))));

  const groups = svg
    .selectAll("g")
    .data(filteredData)
    .enter()
    .append("g")
    .attr("class", "civ");

  const tooltip = d3.select(document.createElement("div")).call(createTooltip);

  const line = svg
    .append("line")
    .attr("y1", 10)
    .attr("y2", height)
    .attr("stroke", "rgba(0,0,0,0.2)")
    .style("pointer-events", "none");

  groups.attr("transform", (d, i) => `translate(0 ${yPositionScale(i)})`);

  groups
    .each(getRect)
    .on("mouseover", function (d) {
      d3.select(this).select("rect").attr("fill", d.color.darker());

      tooltip.style("opacity", 1).html(getTooltipContent(d));
    })
    .on("mouseleave", function (d) {
      d3.select(this).select("rect").attr("fill", d.color);
      tooltip.style("opacity", 0);
    });

  svg
    .append("g")
    .call(axisTop);

  svg
    .append("g")
    .attr("transform", (d, i) => `translate(0 ${height})`)
    .call(axisBottom);

  svg.on("mousemove", function (d) {
    let [x, y] = d3.mouse(this);
    line.attr("transform", `translate(${x} 0)`);
    y += 20;
    if (x > width / 2) x -= 100;

    tooltip.style("left", x + "px").style("top", y + "px");
  });
}
