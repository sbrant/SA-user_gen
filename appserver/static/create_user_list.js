require([
        "splunkjs/mvc",
        "splunkjs/mvc/searchmanager",
        "splunkjs/mvc/simplexml/ready!"
    ], function(mvc, SearchManager) {

    $('#btn_refreshuserlist').click(function(){ 
        splunkjs.mvc.Components.getInstance('userlists').startSearch()
    }); 

    var mysearch = new SearchManager({
        id: "mysearch",
        preview: true,
        cache: true,
        status_buckets: 300,
        search: "",
        autostart: false
    });
    
    $('#btn_mkuserlist').click(function(){ 
        var tokens = mvc.Components.get("default");
        var numplayers = tokens.get("numplayers");
        var pwlen = tokens.get("pwlen");
        var scoringurl = tokens.get("scoringurl");
        var searchurls = tokens.get("searchurls");
        var eventname = tokens.get("eventname");
        var userlistname = tokens.get("userlistname");

        mysearch.settings.set("search", `| makeresults \
                                         | eval numplayers=${numplayers}, pwlen=${pwlen}, eventname="${eventname}", searchurls="${searchurls}", scoringurl="${scoringurl}" \
                                         | usergen \
                                         | fields DisplayUsername Team Password Email ScoringUrl SearchUrl Username Event \
                                         | outputlookup ${userlistname}.csv`
                            );
        mysearch.startSearch();
    });

    mysearch.on("search:done", function() {
        splunkjs.mvc.Components.getInstance('userlists').startSearch();

        var tokens = mvc.Components.get("default");
        var userlistname = tokens.get("userlistname");
        splunkjs.mvc.Components.getInstance('usergenresults').settings.set("search", `| inputlookup ${userlistname}.csv`);
        splunkjs.mvc.Components.getInstance('usergenresults').startSearch();
    });
});