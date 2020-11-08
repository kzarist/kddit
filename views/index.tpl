% xhtml()
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"   
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>{{title}}</title>
    <link rel="stylesheet" type="text/css" href="/static/style.css"/>
    <link rel="icon" href="/static/favicon.svg" sizes="any" type="image/svg+xml"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <meta charset="UTF-8"/>
  </head>
  <body class="background">
    <div class="header">
      {{!header}}
    </div>    
    <div class="content">
      {{!content}}
    </div>
    % if defined("nav"):
      {{!nav}}
    % end
  </body>
</html>
