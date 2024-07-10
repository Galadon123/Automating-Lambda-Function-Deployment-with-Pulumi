exports.handler = async (event) => {
    try {
      let response;
      switch (event.httpMethod) {
        case 'GET':
          if (event.path === '/default/my-lambda-function') {
            response = {
              statusCode: 200,
              body: JSON.stringify('Hello from Lambda Function !'),
            };
          } else if (event.path === '/default/my-lambda-function/test1') {
            response = {
              statusCode: 200,
              body: JSON.stringify('This is test1 route  !!'),
            };
          } else if (event.path === '/default/my-lambda-function/test2') {
            response = {
              statusCode: 200,
              body: JSON.stringify('This is test2 route !'),
            };
          } else {
            response = {
              statusCode: 404,
              body: JSON.stringify('Not Found'),
            };
          }
          break;
        default:
          response = {
            statusCode: 405,
            body: JSON.stringify('Method Not Allowed'),
          };
      }
  
      return response;
    } catch (error) {
      console.error('Handler error:', error);
      return {
        statusCode: 500,
        body: JSON.stringify('Internal Server Error'),
      };
    }
  };
  