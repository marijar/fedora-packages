<% import tg %>
<div class="count-summary-dashboard">
  <div class="overlay"><div class="message"></div></div>
    <script type="text/javascript">
        function got_bug_stats(json) {
            $('#${w.id}_open_bugs').text(json.results.open);
            $('#${w.id}_blockers').text(json.results.blockers);
            $('#${w.id}_blocker_url').attr('href', json.blocker_url);
            $('#${w.id}_num_new_this_week').text(json.results.new_this_week);
            $('#${w.id}_num_closed_this_week').text(json.results.closed_this_week);
        }
        $(document).ready(function(){

fcomm.connector_load('bugzilla', 'get_bug_stats', {package: '${w.package}'}, got_bug_stats, $(".count-summary-dashboard .overlay"));
        });
    </script>
    <form style="float:left; margin-left: 10px;">
        <div id="filter" class="grid_filter" name="release_filter">
            <label style="display: block;" for="version">Release:</label>
            <select name="version">
                <option selected="selected" value="">All Dists</option>
                % for (i, rel) in enumerate(w.release_table):
                    <option value="${rel['value']}">${rel['label']}</option>
                % endfor
            </select>
        </div>
    </form>
    <div class="bugs">
    <div class= "bugs-divs">
    <h3> TOTAL: </h3>
    <dl class="count-box">
       <dt class="count-header main-count-header">Open Bugs</dt>
       <a href="${w.bz_prefix}?${w.base_query_string}&${w.status_open_string}" target="_blank">
         <dd class="main-count-value" id="${w.id}_open_bugs">${w.num_open}</dd>
       </a>
    </dl>
    <dl class="count-box">
       <dt class="count-header main-count-header">Blocking Bugs</dt>
       <a id="${w.id}_blocker_url" href="#" target="_blank">
         <dd class="main-count-value" id="${w.id}_blockers"></dd>
       </a>
    </dl>
    </div>
    <div class="bugs-divs">
    <h3> THIS WEEK: </h3>
    <dl class="count-box">
       <dt class="count-header main-count-header">Closed Bugs</dt>
       <a href="${w.bz_prefix}?${w.base_query_string}&${w.closed_query_string}" target="_blank">
         <dd class="main-count-value" id="${w.id}_num_closed_this_week">${w.num_closed_this_week}</dd>
       </a>
    </dl>
    <dl class="count-box">
       <dt class="count-header main-count-header">New Bugs</dt>
       <a href="${w.bz_prefix}?${w.base_query_string}&${w.open_query_string}" target="_blank">
         <dd class="main-count-value" id="${w.id}_num_new_this_week">${w.num_new_this_week}</dd>
       </a>
    </dl>
    </div>
    <div class="bugs-divs">
    <h3> Open a Bug: </h3>
    <div class="action-box"><a class="action-header"
        target="_blank" href="https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora&version=${w.version}&component=${w.package}">Open A New Bug (Fedora)<br /> <img src="${tg.url('/images/action-box_add-button.png')}"></a>
    </div>
    <div class="action-box"><a class="action-header"
        target="_blank" href="https://bugzilla.redhat.com/enter_bug.cgi?product=Fedora EPEL&version=${w.epel_version}&component=${w.package}">Open A New Bug (EPEL)<br /> <img src="${tg.url('/images/action-box_add-button.png')}"></a>
    </div>
    </div>
    </div>
<div class="clear" />
</div>
