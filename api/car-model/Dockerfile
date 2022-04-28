FROM 491431825058.dkr.ecr.us-east-1.amazonaws.com/insurance:model-base-latest

# add shared code
COPY layers/dependencies/python/lib lib/

COPY api/car-model/*.py ./

# Command can be overwritten by providing a different command in the template directly.
CMD ["app.lambda_handler"]
