FROM 491431825058.dkr.ecr.us-east-1.amazonaws.com/insurance:python-base-latest

# add shared code
COPY layers/dependencies/python/lib ./lib/

# add handler code
COPY api/user/login/*.py ./

# Command can be overwritten by providing a different command in the template directly.
CMD ["app.lambda_handler"]

